SETTING=transformer_vaswani_wmt_en_fr_big

CUDA_VISIBLE_DEVICES=0,1,2,3 python train.py data-bin/wmt14_en_fr \
--arch $SETTING --share-all-embeddings \
  --optimizer adam --adam-betas '(0.9, 0.98)' --clip-norm 0.0 \
  --lr-scheduler inverse_sqrt --warmup-init-lr 1e-07 --warmup-updates 4000 \
  --lr 0.001 --min-lr 1e-09  \
  --dropout 0.3 --weight-decay 0.0 --criterion label_smoothed_cross_entropy --label-smoothing 0.1 \
  --update-freq 64 \
  --max-tokens 2048 --save-dir checkpoints/wmt14.en-fr.joined-dict.transformer