# Copyright (c) 2017-present, Facebook, Inc.
# All rights reserved.
#
# This source code is licensed under the license found in the LICENSE file in
# the root directory of this source tree. An additional grant of patent rights
# can be found in the PATENTS file in the same directory.

import torch
import torch.nn as nn
import torch.nn.functional as F
import math

from fairseq import options, utils

from . import (
    FairseqEncoder, FairseqIncrementalDecoder, FairseqModel, register_model,
    register_model_architecture,
)


@register_model('gru')
class GRUModel(FairseqModel):
    def __init__(self, encoder, decoder):
        super().__init__(encoder, decoder)

    @staticmethod
    def add_args(parser):
        """Add model-specific arguments to the parser."""
        parser.add_argument('--dropout', default=0.1, type=float, metavar='D',
                            help='dropout probability')
        parser.add_argument('--encoder-embed-dim', type=int, metavar='N',
                            help='encoder embedding dimension')
        parser.add_argument('--encoder-embed-path', default=None, type=str, metavar='STR',
                            help='path to pre-trained encoder embedding')
        parser.add_argument('--encoder-hidden-size', type=int, metavar='N',
                            help='encoder hidden size')
        parser.add_argument('--encoder-layers', type=int, metavar='N',
                            help='number of encoder layers')
        parser.add_argument('--encoder-bidirectional', action='store_true',
                            help='make all layers of encoder bidirectional')
        parser.add_argument('--decoder-embed-dim', type=int, metavar='N',
                            help='decoder embedding dimension')
        parser.add_argument('--decoder-embed-path', default=None, type=str, metavar='STR',
                            help='path to pre-trained decoder embedding')
        parser.add_argument('--decoder-hidden-size', type=int, metavar='N',
                            help='decoder hidden size')
        parser.add_argument('--decoder-layers', type=int, metavar='N',
                            help='number of decoder layers')
        parser.add_argument('--decoder-out-embed-dim', type=int, metavar='N',
                            help='decoder output embedding dimension')
        parser.add_argument('--decoder-attention', type=str, metavar='BOOL',
                            help='decoder attention')

        # Granular dropout settings (if not specified these default to --dropout)
        parser.add_argument('--encoder-dropout-in', type=float, metavar='D',
                            help='dropout probability for encoder input embedding')
        parser.add_argument('--encoder-dropout-out', type=float, metavar='D',
                            help='dropout probability for encoder output')
        parser.add_argument('--decoder-dropout-in', type=float, metavar='D',
                            help='dropout probability for decoder input embedding')
        parser.add_argument('--decoder-dropout-out', type=float, metavar='D',
                            help='dropout probability for decoder output')
        
        # Sentense Length control setting
        parser.add_argument('--encoder-max-src-length', type=int, metavar='N',
                            help='max input sentence')
        parser.add_argument('--decoder-max-tgt-length', type=int, metavar='N',
                            help='max output sentence')

        # params freeze setting
        parser.add_argument('--encoder-embed-freeze', action='store_true',
                            help='freeze encoder embedding')
        parser.add_argument('--decoder-embed-freeze', action='store_true',
                            help='freeze decoder embedding')

    @classmethod
    def build_model(cls, args, task):
        """Build a new model instance."""
        # make sure that all args are properly defaulted (in case there are any new ones)
        base_architecture(args)

        def load_pretrained_embedding_from_file(embed_path, dictionary, embed_dim):
            num_embeddings = len(dictionary)
            padding_idx = dictionary.pad()
            embed_tokens = Embedding(num_embeddings, embed_dim, padding_idx)
            embed_dict = utils.parse_embedding(embed_path)
            utils.print_embed_overlap(embed_dict, dictionary)
            return utils.load_embedding(embed_dict, dictionary, embed_tokens)

        pretrained_encoder_embed = None
        if args.encoder_embed_path:
            pretrained_encoder_embed = load_pretrained_embedding_from_file(
                args.encoder_embed_path, task.source_dictionary, args.encoder_embed_dim)
        pretrained_decoder_embed = None
        if args.decoder_embed_path:
            pretrained_decoder_embed = load_pretrained_embedding_from_file(
                args.decoder_embed_path, task.target_dictionary, args.decoder_embed_dim)

        encoder = GRUEncoder(
            dictionary=task.source_dictionary,
            embed_dim=args.encoder_embed_dim,
            hidden_size=args.encoder_hidden_size,
            num_layers=args.encoder_layers,
            dropout_in=args.encoder_dropout_in,
            dropout_out=args.encoder_dropout_out,
            bidirectional=args.encoder_bidirectional,
            pretrained_embed=pretrained_encoder_embed,
            max_src_length=args.encoder_max_src_length,
            embed_freeze=args.encoder_embed_freeze,
        )
        decoder = GRUDecoder(
            dictionary=task.target_dictionary,
            embed_dim=args.decoder_embed_dim,
            hidden_size=args.decoder_hidden_size,
            out_embed_dim=args.decoder_out_embed_dim,
            num_layers=args.decoder_layers,
            dropout_in=args.decoder_dropout_in,
            dropout_out=args.decoder_dropout_out,
            attention=options.eval_bool(args.decoder_attention),
            encoder_embed_dim=args.encoder_embed_dim,
            encoder_hidden_size=args.encoder_hidden_size,
            encoder_output_units=encoder.output_units,
            pretrained_embed=pretrained_decoder_embed,
            max_tgt_length=args.decoder_max_tgt_length,
            embed_freeze=args.decoder_embed_freeze
        )
        return cls(encoder, decoder)


class GRUEncoder(FairseqEncoder):
    """GRU encoder."""
    def __init__(
        self, dictionary, embed_dim=512, hidden_size=512, num_layers=1,
        dropout_in=0.1, dropout_out=0.1, bidirectional=False,
        left_pad=True, pretrained_embed=None, padding_value=0.,
        max_src_length=None, embed_freeze=False,
    ):
        super().__init__(dictionary)
        self.num_layers = num_layers
        self.dropout_in = dropout_in
        self.dropout_out = dropout_out
        self.bidirectional = bidirectional
        self.hidden_size = hidden_size
        self.max_src_length = max_src_length

        num_embeddings = len(dictionary)
        self.padding_idx = dictionary.pad()
        if pretrained_embed is None:
            self.embed_tokens = Embedding(num_embeddings, embed_dim, self.padding_idx)
        else:
            self.embed_tokens = pretrained_embed

        if embed_freeze:
            self.embed_tokens.weight.requires_grad = False

        self.lstm = GRU(
            input_size=embed_dim,
            hidden_size=hidden_size,
            num_layers=num_layers,
            dropout=self.dropout_out if num_layers > 1 else 0.,
            bidirectional=bidirectional,
        )
        self.left_pad = left_pad
        self.padding_value = padding_value

        self.output_units = hidden_size
        if bidirectional:
            self.output_units *= 2

    def forward(self, src_tokens, src_lengths):
        if self.left_pad:
            # convert left-padding to right-padding
            src_tokens = utils.convert_padding_direction(
                src_tokens,
                self.padding_idx,
                left_to_right=True,
            )

        bsz, seqlen = src_tokens.size()

        # embed tokens
        x = self.embed_tokens(src_tokens)
        x = F.dropout(x, p=self.dropout_in, training=self.training)

        # B x T x C -> T x B x C
        x = x.transpose(0, 1)

        # pack embedded source tokens into a PackedSequence
        packed_x = nn.utils.rnn.pack_padded_sequence(x, src_lengths.data.tolist())

        # apply LSTM
        if self.bidirectional:
            state_size = 2 * self.num_layers, bsz, self.hidden_size
        else:
            state_size = self.num_layers, bsz, self.hidden_size
        h0 = x.data.new(*state_size).zero_()
        packed_outs, final_hiddens = self.lstm(packed_x, h0)

        # unpack outputs and apply dropout
        x, _ = nn.utils.rnn.pad_packed_sequence(packed_outs, padding_value=self.padding_value)
        x = F.dropout(x, p=self.dropout_out, training=self.training)
        assert list(x.size()) == [seqlen, bsz, self.output_units]

        if self.bidirectional:

            def combine_bidir(outs):
                return torch.cat([
                    torch.cat([outs[2 * i], outs[2 * i + 1]], dim=0).view(1, bsz, self.output_units)
                    for i in range(self.num_layers)
                ], dim=0)

            final_hiddens = combine_bidir(final_hiddens)

        encoder_padding_mask = src_tokens.eq(self.padding_idx).t()

        return {
            'encoder_out': (x, final_hiddens),
            'encoder_padding_mask': encoder_padding_mask if encoder_padding_mask.any() else None
        }

    def reorder_encoder_out(self, encoder_out_dict, new_order):
        encoder_out_dict['encoder_out'] = tuple(
            eo.index_select(1, new_order)
            for eo in encoder_out_dict['encoder_out']
        )
        if encoder_out_dict['encoder_padding_mask'] is not None:
            encoder_out_dict['encoder_padding_mask'] = \
                encoder_out_dict['encoder_padding_mask'].index_select(1, new_order)
        return encoder_out_dict

    def max_positions(self):
        """Maximum input length supported by the encoder."""
        return self.max_src_length or int(1e5)  # an arbitrary large number
        #return int(1e5)

class BahdanauAttentionLayer(nn.Module):
    def __init__(self, input_embed_dim, output_embed_dim):
        super().__init__()
        
        self.input_proj = NormalLinear(input_embed_dim + output_embed_dim,
            output_embed_dim, bias=False)
        self.v_proj = ZeroLinear(output_embed_dim, 1, bias=False)

    def forward(self, input, source_hids, encoder_padding_mask):
        # input: bsz x input_embed_dim
        # source_hids: srclen x bsz x output_embed_dim

        # x: srclen x bsz x input_embed
        srclen = source_hids.size(0)
        x = input.unsqueeze(0).expand(srclen, -1, -1)

        # x: srclen x bsz x (input_embed + output_embed)
        x = torch.cat((x, source_hids), 2)

        # attn_scores: srclen x bsz x 1
        attn_scores = self.v_proj(F.tanh(self.input_proj(x.view(-1, x.size(2)))))
        attn_scores = attn_scores.view(srclen, -1)

        # don't attend over padding
        if encoder_padding_mask is not None:
            attn_scores = attn_scores.float().masked_fill_(
                encoder_padding_mask,
                float('-inf')
            ).type_as(attn_scores)  # FP16 support: cast to float and back

        attn_scores = F.softmax(attn_scores, dim=0)  # srclen x bsz

        # sum weighted sources
        x = (attn_scores.unsqueeze(2) * source_hids).sum(dim=0)

        return x, attn_scores


class GRUDecoder(FairseqIncrementalDecoder):
    """GRU decoder."""
    def __init__(
        self, dictionary, embed_dim=512, hidden_size=512, out_embed_dim=512,
        num_layers=1, dropout_in=0.1, dropout_out=0.1, attention=True,
        encoder_embed_dim=512, encoder_hidden_size=512, encoder_output_units=512, pretrained_embed=None,
        max_tgt_length=None, embed_freeze=False,
    ):
        super().__init__(dictionary)
        self.dropout_in = dropout_in
        self.dropout_out = dropout_out
        self.hidden_size = hidden_size
        self.max_tgt_length = max_tgt_length

        num_embeddings = len(dictionary)
        padding_idx = dictionary.pad()
        if pretrained_embed is None:
            self.embed_tokens = Embedding(num_embeddings, embed_dim, padding_idx)
        else:
            self.embed_tokens = pretrained_embed

        if embed_freeze:
            self.embed_tokens.weight.requires_grad=False

        self.encoder_output_units = encoder_output_units
        assert encoder_output_units == hidden_size, \
            'encoder_output_units ({}) != hidden_size ({})'.format(encoder_output_units, hidden_size)
        # TODO another Linear layer if not equal

        input_sizes = [hidden_size for layer in range(num_layers)]
        input_sizes[0] = encoder_output_units + embed_dim 
        if attention:
            input_sizes[-1] += encoder_hidden_size

        self.layers = nn.ModuleList([
            GRUCell(
                input_size=input_sizes[i],
                hidden_size=hidden_size,
            )
            for i, layer in enumerate(range(num_layers))
        ])
        self.attention = BahdanauAttentionLayer(encoder_output_units, hidden_size) if attention else None
        if hidden_size != out_embed_dim:
            self.additional_fc = NormalLinear(hidden_size, out_embed_dim)
        self.fc_out = NormalLinear(out_embed_dim, num_embeddings, dropout=dropout_out)

    def forward(self, prev_output_tokens, encoder_out_dict, incremental_state=None):
        encoder_out = encoder_out_dict['encoder_out']
        encoder_padding_mask = encoder_out_dict['encoder_padding_mask']

        if incremental_state is not None:
            prev_output_tokens = prev_output_tokens[:, -1:]
        bsz, seqlen = prev_output_tokens.size()

        # get outputs from encoder
        encoder_outs, _ = encoder_out[:2]
        srclen = encoder_outs.size(0)

        # embed tokens
        x = self.embed_tokens(prev_output_tokens)
        x = F.dropout(x, p=self.dropout_in, training=self.training)

        # B x T x C -> T x B x C
        x = x.transpose(0, 1)

        # initialize previous states (or get from cache during incremental generation)
        cached_state = utils.get_incremental_state(self, incremental_state, 'cached_state')
        if cached_state is not None:
            prev_hiddens, input_feed = cached_state
        else:
            _, encoder_hiddens = encoder_out[:2]
            num_layers = len(self.layers)
            prev_hiddens = [encoder_hiddens[i] for i in range(num_layers)]
            input_feed = x.data.new(bsz, self.encoder_output_units).zero_()

        attn_scores = x.data.new(srclen, seqlen, bsz).zero_()
        outs = []
        for j in range(seqlen):
            # input feeding: concatenate context vector from previous time step
            input = torch.cat((x[j, :, :], input_feed), dim=1)

            for i, rnn in enumerate(self.layers):
                is_last = (i == len(self.layers) - 1)
                if is_last and self.attention is not None:
                    # apply attention using the last layer's hidden state
                    context, attn_scores[:, j, :] = self.attention(prev_hiddens[-1], encoder_outs, encoder_padding_mask)

                    # bsz x embed
                    input = torch.cat((input, context), 1)

                # recurrent cell
                hidden = rnn(input, prev_hiddens[i])

                # hidden state becomes the input to the next layer
                input = F.dropout(hidden, p=self.dropout_out, training=self.training)

                # save state for next time step
                prev_hiddens[i] = hidden

            out = F.dropout(input, p=self.dropout_out, training=self.training)

            # input feeding
            input_feed = out

            # save final output
            outs.append(out)

        # cache previous states (no-op except during incremental generation)
        utils.set_incremental_state(
            self, incremental_state, 'cached_state', (prev_hiddens, input_feed))

        # collect outputs across time steps
        x = torch.cat(outs, dim=0).view(seqlen, bsz, self.hidden_size)

        # T x B x C -> B x T x C
        x = x.transpose(1, 0)

        # srclen x tgtlen x bsz -> bsz x tgtlen x srclen
        attn_scores = attn_scores.transpose(0, 2)

        # project back to size of vocabulary
        if hasattr(self, 'additional_fc'):
            x = self.additional_fc(x)
            x = F.dropout(x, p=self.dropout_out, training=self.training)
        x = self.fc_out(x)

        return x, attn_scores

    def reorder_incremental_state(self, incremental_state, new_order):
        super().reorder_incremental_state(incremental_state, new_order)
        cached_state = utils.get_incremental_state(self, incremental_state, 'cached_state')
        if cached_state is None:
            return

        def reorder_state(state):
            if isinstance(state, list):
                return [reorder_state(state_i) for state_i in state]
            return state.index_select(0, new_order)

        new_state = tuple(map(reorder_state, cached_state))
        utils.set_incremental_state(self, incremental_state, 'cached_state', new_state)

    def max_positions(self):
        """Maximum output length supported by the decoder."""
        return self.max_tgt_length or int(1e5)  # an arbitrary large number
        #return int(1e5)


def Embedding(num_embeddings, embedding_dim, padding_idx):
    m = nn.Embedding(num_embeddings, embedding_dim, padding_idx=padding_idx)
    nn.init.normal_(m.weight, 0, 0.01)
    nn.init.constant_(m.weight[padding_idx], 0)
    return m


def GRU(input_size, hidden_size, **kwargs):
    m = nn.GRU(input_size, hidden_size, **kwargs)
    for name, param in m.named_parameters():
        if 'weight' in name:
            nn.init.orthogonal_(param)
        elif 'bias' in name:
            param.data.zero_()
    return m


def GRUCell(input_size, hidden_size, **kwargs):
    m = nn.GRUCell(input_size, hidden_size, **kwargs)
    for name, param in m.named_parameters():
        if 'weight' in name:
            nn.init.orthogonal_(param)
        elif 'bias' in name:
            param.data.zero_()
    return m


def NormalLinear(in_features, out_features, bias=True, dropout=0):
    """Weight-normalized Linear layer (input: N x T x C)"""
    m = nn.Linear(in_features, out_features, bias=bias)
    m.weight.data.normal_(0, 0.001)
    if bias:
        m.bias.data.normal_(0, 0.001)
    return m


def ZeroLinear(in_features, out_features, bias=True, dropout=0):
    """Weight-init-zero Linear layer (input: N x T x C)"""
    m = nn.Linear(in_features, out_features, bias=bias)
    m.weight.data.zero_()
    if bias:
        m.bias.data.zero_()
    return m


@register_model_architecture('gru', 'gru')
def base_architecture(args):
    args.encoder_embed_dim = getattr(args, 'encoder_embed_dim', 512)
    args.encoder_embed_path = getattr(args, 'encoder_embed_path', None)
    args.encoder_hidden_size = getattr(args, 'encoder_hidden_size', args.encoder_embed_dim)
    args.encoder_layers = getattr(args, 'encoder_layers', 1)
    args.encoder_bidirectional = getattr(args, 'encoder_bidirectional', False)
    args.encoder_dropout_in = getattr(args, 'encoder_dropout_in', args.dropout)
    args.encoder_dropout_out = getattr(args, 'encoder_dropout_out', args.dropout)
    args.decoder_embed_dim = getattr(args, 'decoder_embed_dim', 512)
    args.decoder_embed_path = getattr(args, 'decoder_embed_path', None)
    args.decoder_hidden_size = getattr(args, 'decoder_hidden_size', args.decoder_embed_dim)
    args.decoder_layers = getattr(args, 'decoder_layers', 1)
    args.decoder_out_embed_dim = getattr(args, 'decoder_out_embed_dim', 512)
    args.decoder_attention = getattr(args, 'decoder_attention', '1')
    args.decoder_dropout_in = getattr(args, 'decoder_dropout_in', args.dropout)
    args.decoder_dropout_out = getattr(args, 'decoder_dropout_out', args.dropout)
    args.encoder_max_src_length = getattr(args, 'encoder_max_src_length', None)
    args.decoder_max_tgt_length = getattr(args, 'decoder_max_tgt_length', None)
    args.encoder_embed_freeze = getattr(args, 'encoder_embed_freeze', False)
    args.decoder_embed_freeze = getattr(args, 'decoder_embed_freeze', False)

@register_model_architecture('gru', 'gru_bahdanau_wmt_en_fr')
def gru_bahdanau_wmt_en_fr(args):
    args.encoder_embed_dim = getattr(args, 'encoder_embed_dim', 620)
    args.encoder_hidden_size = getattr(args, 'encoder_hidden_size', 1000)
    args.encoder_layers = getattr(args, 'encoder_layers', 1)
    args.encoder_dropout_out = getattr(args, 'encoder_dropout_out', 0)
    args.decoder_embed_dim = getattr(args, 'decoder_embed_dim', 1000)
    args.decoder_layers = getattr(args, 'decoder_layers', 1)
    args.decoder_out_embed_dim = getattr(args, 'decoder_out_embed_dim', 500)
    args.decoder_dropout_out = getattr(args, 'decoder_dropout_out', 0)
    base_architecture(args)