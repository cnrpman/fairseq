CUDA_VISIBLE_DEVICES=1 \
python generate.py data-bin/wmt14_en_de \
  --path checkpoints/wmt14.en-de.joined-dict.transformer/checkpoint_best.pt \
  --batch-size 128 --quiet --beam 5 --remove-bpe --lenpen 0.6