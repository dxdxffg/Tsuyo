import os
import discord
from discord import app_commands
from discord.ext import commands
from transformers import pipeline
import torch
import pandas as pd
import random
from threading import Thread
from http.server import SimpleHTTPRequestHandler, HTTPServer

def run_server():
    server = HTTPServer(('0.0.0.0', 8000), SimpleHTTPRequestHandler)
    server.serve_forever()

Thread(target=run_server, daemon=True).start()
# -----------------------------
# CSV 파일 이름 설정
# -----------------------------
USER_DATA_FILE = 'user_data.csv'
USER_MODE_FILE = 'user_mode.csv'
CSV_FILES = {
    'general': 'general_qa.csv',
    'yandere': 'yandere_qa.csv',
    'custom': 'custom_qa.csv'
}

# -----------------------------
# 칭호 호출 함수
# -----------------------------
def get_title(favorability):
    titles = [
        "수줍은 친구", "다가가는 마음", "말동무", "친근한 동료", "특별한 존재",
        "내 사람", "마음을 훔친 자", "빠져든다", "보고싶은 사람", "생각나는 존재",
        "설레는 마음", "하루의 위로", "당신뿐이야", "헤어나올 수 없어", "완전히 빠졌다",
        "집착하는 마음", "통제불능", "사랑의 포로", "위험한 관계", "놓칠 수 없는 사람",
        "영혼의 동반자", "생명줄", "운명의 상대", "우주 끝까지", "절대적인 존재"
    ]
    index = favorability // 100
    return titles[-1] if index >= len(titles) else titles[index]

# -----------------------------
# 최초 실행 시 빈 파일 생성
# -----------------------------
if not os.path.exists(USER_DATA_FILE):
    pd.DataFrame(columns=['user_id', 'username', 'favorability']).to_csv(USER_DATA_FILE, index=False)
if not os.path.exists(USER_MODE_FILE):
    pd.DataFrame(columns=['user_id', 'mode']).to_csv(USER_MODE_FILE, index=False)

# -----------------------------
# Hugging Face 유사도 모델
# -----------------------------
similarity_model = pipeline("feature-extraction", model="sentence-transformers/all-MiniLM-L6-v2")

# -----------------------------
# 디스코드 봇 설정
# -----------------------------
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="/", intents=intents)

# -----------------------------
# 모드별 헷갈림 대사
# -----------------------------
confused_responses_by_mode = {
    "general": ["***(갸우뚱)***", "? 뭔소리..야?", "뭐라고?", "엥??", "잘 못 들었어.."],
    "yandere": ["후후… 무슨 말이든 귀엽네♥", "뭐야… 모르는 말인데도 귀여워…", "알아듣기 힘들지만… 상관없어, 당신 목소리니까"],
    "custom": ["오오… 새로 배우는 말인가요?", "헤헤… 이건 처음 듣는데요!", "좋아요, 좀 더 알려주세요!"]
}

# -----------------------------
# 유저 호감도 관리 함수
# -----------------------------
def update_favorability(user_id, username, delta=1):
    df = pd.read_csv(USER_DATA_FILE)
    if user_id in df['user_id'].values:
        df.loc[df['user_id'] == user_id, 'favorability'] += delta
    else:
        new_row = pd.DataFrame([[user_id, username, delta]], columns=df.columns)
        df = pd.concat([df, new_row], ignore_index=True)
    df.to_csv(USER_DATA_FILE, index=False)

def get_favorability(user_id):
    df = pd.read_csv(USER_DATA_FILE)
    row = df[df['user_id'] == user_id]
    if row.empty:
        return 0
    return int(row['favorability'].values[0])

# -----------------------------
# 유저 모드 관리 함수
# -----------------------------
def set_mode(user_id, mode):
    df = pd.read_csv(USER_MODE_FILE)
    if user_id in df['user_id'].values:
        df.loc[df['user_id'] == user_id, 'mode'] = mode
    else:
        new_row = pd.DataFrame([[user_id, mode]], columns=df.columns)
        df = pd.concat([df, new_row], ignore_index=True)
    df.to_csv(USER_MODE_FILE, index=False)

def get_mode(user_id):
    df = pd.read_csv(USER_MODE_FILE)
    row = df[df['user_id'] == user_id]
    if row.empty:
        return 'general'
    return row['mode'].values[0]

# -----------------------------
# Q/A CSV 불러오기 함수
# -----------------------------
def load_qa_csv(mode):
    filename = CSV_FILES.get(mode, CSV_FILES['general'])
    df = pd.read_csv(filename)
    return df['question'].tolist(), df['answer'].tolist()

# -----------------------------
# 봇 준비 완료 이벤트
# -----------------------------
@bot.event
async def on_ready():
    print(f'{bot.user}로 로그인됨!')
    await bot.tree.sync()

# -----------------------------
# /모드 명령어
# -----------------------------
@bot.tree.command(name="모드", description="모드를 변경합니다 (일반, 얀데레, 커스텀).")
@app_commands.describe(name="모드 이름")
async def 모드(interaction: discord.Interaction, name: str):
    user_id = interaction.user.id
    favorability = get_favorability(user_id)

    if name == "얀데레" and favorability < 2500:
        await interaction.response.send_message("얀데레 모드는 호감도 2500 이상에서만 가능합니다!")
        return
    if name == "커스텀" and favorability < 5000:
        await interaction.response.send_message("커스텀 모드는 호감도 5000 이상에서만 가능합니다!")
        return

    set_mode(user_id, name)

    embed = discord.Embed(
        title="모드 변경 완료",
        description=f"{interaction.user.mention}님의 모드가 **{name}**로 변경되었습니다!",
        color=discord.Color.green()
    )
    await interaction.response.send_message(embed=embed)

# -----------------------------
# /핑 명령어
# -----------------------------
@bot.tree.command(name="핑", description="봇 지연시간을 보여줍니다.")
async def 핑(interaction: discord.Interaction):
    latency_ms = round(bot.latency * 1000)
    embed = discord.Embed(
        title="퐁!",
        description=f"지연시간: {latency_ms}ms",
        color=discord.Color.orange()
    )
    await interaction.response.send_message(embed=embed)

# -----------------------------
# 메시지 이벤트
# -----------------------------
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    user_id = message.author.id
    username = str(message.author)
    mode = get_mode(user_id)

    if message.content.startswith('츠요야'):
        user_input = message.content[4:].strip()

        if not user_input:
            await message.channel.send("응! 왜..?")
            return

        questions, answers = load_qa_csv(mode)
        input_emb = torch.tensor(similarity_model(user_input)).mean(dim=1)
        candidate_embs = torch.tensor([similarity_model(q)[0][0] for q in questions])
        cosine_sim = torch.nn.functional.cosine_similarity(input_emb, candidate_embs)
        max_score = torch.max(cosine_sim).item()

        if max_score < 0.3:
            best_answer = random.choice(confused_responses_by_mode.get(mode, confused_responses_by_mode['general']))
        else:
            best_idx = torch.argmax(cosine_sim).item()
            best_answer = answers[best_idx]
            update_favorability(user_id, username, delta=1)

        await message.channel.send(f"{best_answer}")

    await bot.process_commands(message)

# -----------------------------
# /프로필 명령어
# -----------------------------
@bot.tree.command(name="프로필", description="나의 호감도와 칭호를 확인합니다.")
async def 프로필(interaction: discord.Interaction):
    user_id = interaction.user.id
    username = str(interaction.user)
    favorability = get_favorability(user_id)
    title = get_title(favorability)

    embed = discord.Embed(
        title=f"{username}님의 프로필",
        description=f"**호감도**: {favorability}점\n**칭호**: {title}",
        color=discord.Color.purple()
    )
    embed.set_thumbnail(url=interaction.user.display_avatar.url)

    await interaction.response.send_message(embed=embed)

# -----------------------------
# 봇 실행 (환경 변수에서 토큰 읽기)
# -----------------------------
TOKEN = os.getenv('DISCORD_TOKEN')
if not TOKEN:
    raise Exception("DISCORD_TOKEN 환경 변수가 설정되지 않았습니다!")
bot.run(TOKEN)
