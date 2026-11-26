# Email drafts

Contents:

1. Rules for every email
2. First pitch to a writer (review key)
3. First pitch to a creator
4. The one follow-up
5. Embargo reminder
6. Reply to a key request
7. Reply to a curator who asks for keys by email
8. Draft file shape

All examples use a made-up game. Write each email fresh for its person. Never send; the user
sends from their own address.

## 1. Rules for every email

- One person per email. Their name in the greeting. No BCC lists, no mail merge that shows.
- Subject: short, with the game's name, the hook and the news. If there is an embargo, put it
  first: `[Embargo 10 Mar, 17:00 UTC]`.
- First line: why them. Name the similar game they covered or played, and link it if you can.
- Then the news in one or two sentences: what the game is and what is happening, with the date.
- Include the key in the email when you offer one. Do not ask if they want one. Writers and
  creators skim: nearly 40% of journalists spent under 20 seconds per email in one survey (Mike
  Rose, old, claim).
- Embargo: date, time and time zone, the same for everyone, press and creators alike.
- Links: the contact's tagged Steam link, the press kit, the trailer. Three links, no more.
- Short. One studied cold email body was 289 characters (Ryan K. Rigney, Push to Talk,
  11 Jul 2025): one sentence with the genre and the hook, the release date about a month away,
  the full store.steampowered.com link, and a request to reply for a key, with a 5 second gameplay
  GIF under the signature. One day later the YouTuber posted a preview with 80,000 views, and
  the game got 6,000 wishlists. Rigney notes that most pitches overwhelm the reader with detail.
  Aim for under 150 words for press, and near that 289 character length for creators.
- Plain text, no attachments over a few MB. Link the press kit instead.
- Only true claims about the current build.
- One line asking the creator to mention that the key was free (Manalens practice). Never make a
  key depend on a positive video.

### AI drafts

An AI tool can draft the hook and the facts from your press kit. You write the first line, from
a video or article you actually read, and you send each email (Manalens practice). Give it only
facts and these rules:

```
Write 3 versions of a cold email to [creator name], who posted a
video of [comparable game] on [date].

Use only these facts:
- Game: [name], [genre]
- Hook: [one sentence]
- Release date: [date]
- Steam link: [full store link with utm_content=<contact slug>]
- What I liked in their video: [your note, one line]

Rules: the body must be under 300 characters. One sentence on the
game and the hook. Ask them to mention the key was free. No hype
words, no claims I did not give you, no questions in the opening line.
```

Then cut the draft, check every claim, date and link, and add the key line from section 2 or 3.
AI drafts tend to run long, so ask for less than you need.

## 2. First pitch to a writer (review key)

```
Subject: [Embargo 10 Mar, 17:00 UTC] Pumpkin Patch: herd 200 walking pumpkins, out 12 March

Hi Sam,

You reviewed Ooblets and Moonstone Island for Cozy Weekly, so I think Pumpkin Patch fits your
readers. It is a cozy farming game where your pumpkins grow legs at night and you herd them to
market by lantern light. It comes out on Steam on 12 March.

Here is a Steam key for review: <key>
Embargo: 10 March, 17:00 UTC, the same for everyone.

Steam: <tagged link for cozy_weekly_sam>
Press kit: <press kit URL>
Trailer: <YouTube URL>

Thanks,
Ana Lopez, Gourd Games
```

## 3. First pitch to a creator

```
Subject: Pumpkin Patch: your Moonstone Island run, but the crops walk away (key inside)

Hi Pip,

I watched your Moonstone Island series, and I think Pumpkin Patch fits your channel. Your
pumpkins grow legs at night, and you herd them to market before sunrise.

Status: full release on Steam on 12 March. Embargo: 10 March, 17:00 UTC.
Here is a Steam key: <key>
You may stream, record and monetise videos of the game. The music is ours and safe to use.

Steam: <tagged link for pipplays>
Press kit: <press kit URL>

Thanks,
Ana
```

Creators must disclose free keys in their videos (FTC in the US, CMA in the UK). The FTC's
guides (16 CFR 255.5) say material connections can include free or discounted products and
early access, and must be disclosed clearly and conspicuously when the audience would not expect
them. Valve asks reviewers to disclose a free copy in a Steam review. Valve allows copies for
previews and reviews, but not rewards for reviews. Do not ask for a positive video, a review
score or a Steam review in return.

## 4. The one follow-up

Send once, about a week after the first email, in the same thread, with one new fact. Then stop
until there is real news. Three or more reminders annoy creators (YouTuber Blitz, via Manalens).

```
Subject: Re: <first subject>

Hi Sam,

A short follow-up on Pumpkin Patch: the launch trailer is out today (<YouTube URL>). The key in my
first email still works, and the embargo is still 10 March, 17:00 UTC.

Thanks,
Ana
```

## 5. Embargo reminder

Only to people who said yes, 2 days before the embargo (IndieGamesPlus).

```
Subject: Pumpkin Patch embargo: 10 March, 17:00 UTC

Hi Sam, a reminder that the embargo lifts on 10 March at 17:00 UTC. Thank you for playing.
Ana
```

## 6. Reply to a key request

Before you send anything, check the request:

1. Open the channel or outlet page yourself. Find the published business email.
2. If the request came from another address, reply to the published one only.
3. Check that the channel is active, plays games like yours, and has real comments.
4. Send one key, from a batch you made for this beat. Log the date and batch, not the key.

```
Hi <name>, thanks for asking. To make sure keys reach the right people, I send them only to the
business email on the channel page. I have sent it there now.
```

## 7. Reply to a curator who asks for keys by email

```
Hi, thank you for your interest. We send all curator copies through Steam Curator Connect, so
please look for it in your curator dashboard. We do not send curator keys by email.
```

Then send the copy through Curator Connect if the curator is real and fits. A real curator can
accept it there; a scammer cannot resell it.

## 8. Draft file shape

`marketing/outreach/emails/<utm_content>.md`:

```markdown
# Cozy Weekly, Sam Writer

- utm_content: cozy_weekly_sam
- Type: press
- Why them: reviewed Ooblets (link), Moonstone Island (link)
- Link: https://store.steampowered.com/app/480/?utm_source=press&utm_medium=email&utm_campaign=launch&utm_content=cozy_weekly_sam
- Send on: 2027-02-17 (3 weeks before the embargo)
- Follow-up on: 2027-02-24

## Pitch
Subject: ...

(body)

## Follow-up
Subject: Re: ...

(body)
```
