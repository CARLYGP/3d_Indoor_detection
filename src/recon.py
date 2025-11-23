from slam3r.pipeline.recon_online_pipeline import scene_recon_pipeline_online, FrameReader
from slam3r.pipeline.recon_offline_pipeline import scene_recon_pipeline_offline
import argparse
from slam3r.utils.recon_utils import *
from slam3r.datasets.wild_seq import Seq_Data
from slam3r.models import Image2PointsModel, Local2WorldModel, inf
from slam3r.utils.device import to_numpy
import os
import torch
import numpy as np


def load_model(model_name, weights, device='cuda'):
    print('Loading model: {:s}'.format(model_name))
    model = eval(model_name)
    model.to(device)
    print('Loading pretrained: ', weights)
    ckpt = torch.load(weights, map_location=device)
    print(model.load_state_dict(ckpt['model'], strict=False))
    del ckpt
    return model


parser = argparse.ArgumentParser(description="Inference on a scene")

parser.add_argument("--device", type=str, default='cuda')

parser.add_argument('--i2p_model', type=str,
                    default="Image2PointsModel(pos_embed='RoPE100', img_size=(224, 224), head_type='linear', output_mode='pts3d', depth_mode=('exp', -inf, inf), conf_mode=('exp', 1, inf), enc_embed_dim=1024, enc_depth=24, enc_num_heads=16, dec_embed_dim=768, dec_depth=12, dec_num_heads=12, mv_dec1='MultiviewDecoderBlock_max',mv_dec2='MultiviewDecoderBlock_max', enc_minibatch = 11)")

parser.add_argument("--l2w_model", type=str,
                    default="Local2WorldModel(pos_embed='RoPE100', img_size=(224, 224), head_type='linear', output_mode='pts3d', depth_mode=('exp', -inf, inf), conf_mode=('exp', 1, inf), enc_embed_dim=1024, enc_depth=24, enc_num_heads=16, dec_embed_dim=768, dec_depth=12, dec_num_heads=12, mv_dec1='MultiviewDecoderBlock_max',mv_dec2='MultiviewDecoderBlock_max', enc_minibatch = 11, need_encoder=False)")

parser.add_argument('--i2p_weights', type=str)
parser.add_argument("--l2w_weights", type=str)

# YA NO obligatorios
parser.add_argument("--dataset", type=str, required=False)
parser.add_argument("--img_dir", type=str, required=False)

parser.add_argument("--save_dir", type=str, default="results")
parser.add_argument("--test_name", type=str, required=True)

parser.add_argument('--save_all_views', action='store_true')

# Scene recon params
parser.add_argument("--keyframe_stride", type=int, default=3)
parser.add_argument("--initial_winsize", type=int, default=5)
parser.add_argument("--win_r", type=int, default=3)
parser.add_argument("--conf_thres_i2p", type=float, default=1.5)
parser.add_argument("--num_scene_frame", type=int, default=10)
parser.add_argument("--max_num_register", type=int, default=10)
parser.add_argument("--conf_thres_l2w", type=float, default=12)
parser.add_argument("--num_points_save", type=int, default=2000000)
parser.add_argument("--norm_input", action="store_true")
parser.add_argument("--save_frequency", type=int, default=3)
parser.add_argument("--save_each_frame", action='store_true', default=True)

# NUEVO → permite video directamente
parser.add_argument("--video_path", type=str)

# Online mode
parser.add_argument("--retrieve_freq", type=int, default=1)
parser.add_argument("--update_buffer_intv", type=int, default=1)
parser.add_argument('--buffer_size', type=int, default=100)
parser.add_argument("--buffer_strategy", type=str,
                    choices=['reservoir', 'fifo'], default='reservoir')
parser.add_argument("--save_online", action='store_true')

# Keyframe auto adapt
parser.add_argument("--keyframe_adapt_min", type=int, default=1)
parser.add_argument("--keyframe_adapt_max", type=int, default=20)
parser.add_argument("--keyframe_adapt_stride", type=int, default=1)
parser.add_argument("--perframe", type=int, default=1)

parser.add_argument("--seed", type=int, default=42)
parser.add_argument('--gpu_id', type=int, default=-1)
parser.add_argument('--save_preds', action='store_true')
parser.add_argument('--save_for_eval', action='store_true')
parser.add_argument("--online", action="store_true")


if __name__ == "__main__":

    args = parser.parse_args()

    if args.gpu_id == -1:
        args.gpu_id = get_free_gpu()

    print("Using GPU:", args.gpu_id)
    torch.cuda.set_device(f"cuda:{args.gpu_id}")

    np.random.seed(args.seed)

    # Load model & weights
    if args.i2p_weights:
        i2p_model = load_model(args.i2p_model, args.i2p_weights, args.device)
    else:
        i2p_model = Image2PointsModel.from_pretrained('siyan824/slam3r_i2p').to(args.device)

    if args.l2w_weights:
        l2w_model = load_model(args.l2w_model, args.l2w_weights, args.device)
    else:
        l2w_model = Local2WorldModel.from_pretrained('siyan824/slam3r_l2w').to(args.device)

    i2p_model.eval()
    l2w_model.eval()

    save_dir = os.path.join(args.save_dir, args.test_name)
    os.makedirs(save_dir, exist_ok=True)

    # ------------------------------------------------------------------
    # ONLINE MODE
    # ------------------------------------------------------------------
    if args.online:

        if args.video_path:
            picture_capture = FrameReader(args.video_path)
        elif args.dataset:
            picture_capture = FrameReader(args.dataset)
        else:
            raise ValueError("Para modo online necesitas --video_path o --dataset")

        scene_recon_pipeline_online(i2p_model, l2w_model, picture_capture, args, save_dir)

    # ------------------------------------------------------------------
    # OFFLINE MODE
    # ------------------------------------------------------------------
    else:

        if args.video_path:
            # Extraemos frames al vuelo desde video
            picture_capture = FrameReader(args.video_path)
            scene_recon_pipeline_online(i2p_model, l2w_model, picture_capture, args, save_dir)
            exit()

        if args.dataset:
            print("Loading dataset:", args.dataset)
            dataset = Seq_Data(img_dir=args.dataset, img_size=224,
                               silent=False, sample_freq=1, start_idx=0, num_views=-1,
                               start_freq=1, to_tensor=True)

        elif args.img_dir:
            dataset = Seq_Data(img_dir=args.img_dir, img_size=224, to_tensor=True)

        else:
            raise ValueError("En modo offline debes usar --dataset, --img_dir o --video_path")

        if hasattr(dataset, "set_epoch"):
            dataset.set_epoch(0)

        scene_recon_pipeline_offline(i2p_model, l2w_model, dataset, args, save_dir)
