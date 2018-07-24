MODEL=bahdanau_lemans_wmt_en_fr
GPUID=1

mkdir -p checkpoints/$MODEL logs
CUDA_VISIBLE_DEVICES=$GPUID python train.py data-bin/lemans-wmt14_en_fr \
  --encoder-embed-freeze --decoder-embed-freeze \
  --lr 0.0001 --lr-scheduler fixed --optimizer sgd \
  --batch-size 80 --clip-norm 1.0 \
  --encoder-max-src-length 52 --decoder-max-tgt-length 52 --skip-invalid-size-inputs-valid-test\
  --criterion cross_entropy --dropout 0.0 \
  --arch gru_bahdanau_wmt_en_fr --save-dir checkpoints/$MODEL