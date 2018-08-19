SETTING=transformer

CUDA_VISIBLE_DEVICES=0,1,2,3 python train.py data-bin/wmt14_en_de \
--arch $SETTING --share-input-output-embed \
  --max-update 100000 \
  --optimizer adam --adam-betas '(0.9, 0.98)' --clip-norm 0.0 \
  --lr-scheduler inverse_sqrt --warmup-init-lr 1e-07 --warmup-updates 4000 \
  --lr 0.00001 --min-lr 1e-09  \
  --dropout 0.1 --weight-decay 0.0 --criterion label_smoothed_cross_entropy --label-smoothing 0.1 \
  --update-freq 2 \
  --max-tokens 3584 --save-dir checkpoints/wmt14.ende.joined-dict.transformer.drop0.005.clip0.0/