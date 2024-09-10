import requests
from bs4 import BeautifulSoup
from requests.exceptions import RequestException
import time
import re
import tkinter as tk
from tkinter import ttk, scrolledtext
import threading

def get_github_users(username, relation_type, max_pages=20):
    base_url = f'https://github.com/{username}?tab={relation_type}'
    session = requests.Session()
    users_list = []
    page = 1

    while page <= max_pages:
        try:
            url = f'{base_url}&page={page}'
            response = session.get(url)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')
            
            user_elements = soup.find_all('a', class_='d-inline-block no-underline mb-1')
            if not user_elements:
                user_elements = soup.find_all('a', {'data-hovercard-type': 'user'})

            if not user_elements:
                break

            for user in user_elements:
                name_span = user.find('span', class_='f4 Link--primary')
                if not name_span:
                    name_span = user.find('span', class_='Link--secondary')
                
                if name_span and name_span.get_text(strip=True):
                    name = name_span.get_text(strip=True)
                    if name != 'Achievements' and not re.match(r'^@', name):
                        users_list.append(name)
                else:
                    href = user.get('href', '')
                    if href.startswith('/'):
                        name = href.split('/')[-1]
                        users_list.append(name)

            page += 1
            time.sleep(1)

        except RequestException as e:
            print(f"Erro ao acessar a página {page} de {relation_type}: {e}")
            break

    return list(dict.fromkeys(users_list))

def get_user_count(username, relation_type):
    try:
        response = requests.get(f'https://github.com/{username}')
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        if relation_type == 'following':
            count_element = soup.find_all('span', class_='text-bold color-fg-default')[1]
        elif relation_type == 'followers':
            count_element = soup.find_all('span', class_='text-bold color-fg-default')[0]
        
        if count_element:
            return int(count_element.text.strip())
    except Exception as e:
        print(f"Erro ao verificar o número de {relation_type}: {e}")
    return None

def compare_lists(following, followers):
    not_following_back = list(set(following) - set(followers))
    return sorted(not_following_back)

def analyze_github_user(username, result_text, progress, analyze_button):
    result_text.delete('1.0', tk.END)
    result_text.insert(tk.END, f"Analisando o usuário: {username}\n\n")

    # Obtém a lista de pessoas que o usuário está seguindo
    following = get_github_users(username, 'following')
    following_count = get_user_count(username, 'following')
    result_text.insert(tk.END, f"Pessoas que {username} está seguindo: {following_count}\n")

    # Obtém a lista de seguidores do usuário
    followers = get_github_users(username, 'followers')
    followers_count = get_user_count(username, 'followers')
    result_text.insert(tk.END, f"Pessoas que seguem {username}: {followers_count}\n")

    # Compara as listas e mostra quem o usuário segue mas não o segue de volta
    not_following_back = compare_lists(following, followers)
    result_text.insert(tk.END, f"\nPessoas que você segue mas não te seguem de volta ({len(not_following_back)}):\n")
    for name in not_following_back:
        result_text.insert(tk.END, f"{name}\n")

    # Oculta o indicador de progresso e reativa o botão
    progress.stop()
    progress.grid_remove()
    analyze_button.config(state=tk.NORMAL)

def start_analysis(username_entry, result_text, progress, analyze_button):
    username = username_entry.get()
    if username:
        # Desativa o botão e mostra o indicador de progresso
        analyze_button.config(state=tk.DISABLED)
        progress.grid()
        progress.start()

        # Inicia a análise em uma thread separada
        threading.Thread(target=analyze_github_user, args=(username, result_text, progress, analyze_button)).start()
    else:
        result_text.delete('1.0', tk.END)
        result_text.insert(tk.END, "Por favor, insira um nome de usuário.")

def create_gui():
    root = tk.Tk()
    root.title("Analisador de Seguidores do GitHub")
    root.geometry("600x400")

    frame = ttk.Frame(root, padding="10")
    frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)

    ttk.Label(frame, text="Nome de usuário do GitHub:").grid(column=0, row=0, sticky=tk.W)
    username_entry = ttk.Entry(frame, width=30)
    username_entry.grid(column=1, row=0, sticky=(tk.W, tk.E))

    result_text = scrolledtext.ScrolledText(frame, wrap=tk.WORD, width=70, height=20)
    result_text.grid(column=0, row=2, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))

    # Cria o indicador de progresso circular
    progress = ttk.Progressbar(frame, orient=tk.HORIZONTAL, length=200, mode='indeterminate')
    progress.grid(column=0, row=1, columnspan=2, pady=10)
    progress.grid_remove()  # Inicialmente oculto

    analyze_button = ttk.Button(frame, text="Analisar", 
                                command=lambda: start_analysis(username_entry, result_text, progress, analyze_button))
    analyze_button.grid(column=1, row=0, sticky=tk.E)

    for child in frame.winfo_children(): 
        child.grid_configure(padx=5, pady=5)

    frame.columnconfigure(1, weight=1)
    frame.rowconfigure(2, weight=1)

    root.mainloop()

if __name__ == "__main__":
    create_gui()