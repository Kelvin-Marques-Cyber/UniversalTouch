"""CLI keeps help/version light; imports vision only when explicitly needed."""
import argparse
import json
import os

from . import __version__


def main():
    parser = argparse.ArgumentParser(description='UniversalTouch · controle local por gestos da mão')
    parser.add_argument('--version',action='version',version=f'UniversalTouch {__version__}')
    parser.add_argument('--camera',type=int,default=0,help='índice da câmera (padrão: 0)')
    parser.add_argument('--fps',type=int,choices=range(5,31),metavar='5..30',default=15,help='limite de processamento (padrão econômico: 15)')
    parser.add_argument('--self-test',action='store_true',help='verificar modelos sem abrir câmera nem enviar eventos')
    parser.add_argument('--benchmark',type=float,metavar='SEGUNDOS',help='medir câmera, inferência, memória e CPU sem controlar o mouse')
    parser.add_argument('--gui-smoke-test',type=float,help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.camera < 0: parser.error('--camera deve ser zero ou maior')
    if args.benchmark is not None and not .5 <= args.benchmark <= 60:
        parser.error('--benchmark deve ficar entre 0.5 e 60 segundos')
    for name in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:
        os.environ[name] = '1'
    try:
        if args.self_test:
            from .vision import self_test
            print(json.dumps(self_test(),ensure_ascii=False,indent=2))
            return 0
        if args.benchmark is not None:
            from .vision import benchmark
            print(json.dumps(benchmark(args.benchmark,args.camera),ensure_ascii=False,indent=2))
            return 0
        from .app import run
        return run(args.camera,args.fps,args.gui_smoke_test)
    except Exception as exc:
        parser.exit(1,f'UniversalTouch: {exc}\n')


if __name__ == '__main__':
    raise SystemExit(main())
