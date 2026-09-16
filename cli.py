from agent import run_turn_streaming
from svg import render_svg

def main():
    canvas=[]; messages=[]
    print("Diagram Agent. Type 'quit' to exit.")
    while True:
        try: prompt=input('you › ').strip()
        except (EOFError, KeyboardInterrupt): print(); break
        if prompt.lower() in {'quit','exit'}: break
        if not prompt: continue
        messages.append({'role':'user','content':prompt}); print('agent › ', end='', flush=True)
        run_turn_streaming(messages, canvas); render_svg(canvas); print('[canvas.svg refreshed]')
if __name__ == '__main__': main()
