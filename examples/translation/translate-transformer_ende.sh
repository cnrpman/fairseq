CUDA_VISIBLE_DEVICES=1 \
python generate.py data-bin/wmt14_en_de \
  --path checkpoints/wmt14.ende.joined-dict.transformer.drop0.005.clip0.0/checkpoint_best.pt \
  --batch-size 128 --quiet --beam 5 --remove-bpe --lenpen 0.6