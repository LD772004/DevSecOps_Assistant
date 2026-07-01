from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable, KeepTogether
)
from reportlab.platypus.flowables import Flowable
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor

# ─── Color palette ────────────────────────────────────────────────────────────
PRIMARY   = HexColor('#1A1A2E')
ACCENT    = HexColor('#3B82F6')
GOLD      = HexColor('#F59E0B')
LIGHT_BG  = HexColor('#F3F0E8')
CODE_BG   = HexColor('#1E1E2E')
CODE_FG   = HexColor('#CDD6F4')
GREEN     = HexColor('#22C55E')
PURPLE    = HexColor('#7C3AED')
GRAY      = HexColor('#6B7280')
WHITE     = colors.white
BLACK     = colors.black
LIGHT_ACCENT = HexColor('#EFF6FF')

PAGE_W, PAGE_H = A4

# ─── Code block flowable ──────────────────────────────────────────────────────
class CodeBlock(Flowable):
    def __init__(self, text, width=None):
        Flowable.__init__(self)
        self.text = text
        self._width = width or (PAGE_W - 4*cm)
        self.lines = text.split('\n')
        self._height = len(self.lines) * 13 + 16

    def wrap(self, availWidth, availHeight):
        return self._width, self._height

    def draw(self):
        c = self.canv
        c.setFillColor(CODE_BG)
        c.roundRect(0, 0, self._width, self._height, 5, fill=1, stroke=0)
        c.setFillColor(ACCENT)
        c.roundRect(0, 0, 4, self._height, 2, fill=1, stroke=0)
        c.setFont('Courier', 8.5)
        c.setFillColor(CODE_FG)
        y = self._height - 12
        for line in self.lines:
            c.drawString(12, y, line)
            y -= 13


class FeatureBox(Flowable):
    def __init__(self, title, items, width=None):
        Flowable.__init__(self)
        self.title = title
        self.items = items
        self._width = width or (PAGE_W - 4*cm)
        self._height = 26 + len(items) * 18 + 10

    def wrap(self, availWidth, availHeight):
        return self._width, self._height

    def draw(self):
        c = self.canv
        # Box background
        c.setFillColor(LIGHT_ACCENT)
        c.roundRect(0, 0, self._width, self._height, 6, fill=1, stroke=0)
        # Accent border
        c.setStrokeColor(ACCENT)
        c.setLineWidth(1.5)
        c.roundRect(0, 0, self._width, self._height, 6, fill=0, stroke=1)
        # Title bar
        c.setFillColor(ACCENT)
        c.roundRect(0, self._height-26, self._width, 26, 6, fill=1, stroke=0)
        c.rect(0, self._height-26, self._width, 13, fill=1, stroke=0)
        c.setFillColor(WHITE)
        c.setFont('Helvetica-Bold', 10)
        c.drawString(10, self._height - 17, self.title)
        # Items
        c.setFillColor(PRIMARY)
        c.setFont('Helvetica', 9)
        y = self._height - 44
        for item in self.items:
            c.setFillColor(ACCENT)
            c.circle(10, y + 4, 3, fill=1, stroke=0)
            c.setFillColor(PRIMARY)
            c.drawString(20, y, item)
            y -= 18


class NoteBox(Flowable):
    def __init__(self, text, width=None):
        Flowable.__init__(self)
        self.text = text
        self._width = width or (PAGE_W - 4*cm)
        self._height = 44

    def wrap(self, availWidth, availHeight):
        return self._width, self._height

    def draw(self):
        c = self.canv
        c.setFillColor(HexColor('#EFF6FF'))
        c.roundRect(0, 0, self._width, self._height, 4, fill=1, stroke=0)
        c.setStrokeColor(ACCENT)
        c.setLineWidth(1)
        c.roundRect(0, 0, self._width, self._height, 4, fill=0, stroke=1)
        c.setFillColor(ACCENT)
        c.setFont('Helvetica-Bold', 9)
        c.drawString(10, self._height - 15, 'NOTE')
        c.setFillColor(PRIMARY)
        c.setFont('Helvetica', 8.5)
        # Simple text wrap
        words = self.text.split()
        line, lines = [], []
        for w in words:
            line.append(w)
            if len(' '.join(line)) > 95:
                lines.append(' '.join(line[:-1]))
                line = [w]
        if line:
            lines.append(' '.join(line))
        y = self._height - 28
        for l in lines[:2]:
            c.drawString(10, y, l)
            y -= 13


# ─── Page templates ───────────────────────────────────────────────────────────
def cover_page(canvas_obj, doc):
    canvas_obj.saveState()
    w, h = PAGE_W, PAGE_H
    # Dark background
    canvas_obj.setFillColor(PRIMARY)
    canvas_obj.rect(0, 0, w, h, fill=1, stroke=0)
    # Top accent bar
    canvas_obj.setFillColor(ACCENT)
    canvas_obj.rect(0, h - 8, w, 8, fill=1, stroke=0)
    # Bottom accent bar
    canvas_obj.rect(0, 0, w, 6, fill=1, stroke=0)
    # Side accent
    canvas_obj.setFillColor(GOLD)
    canvas_obj.rect(0, 0, 6, h, fill=1, stroke=0)

    # Title
    canvas_obj.setFillColor(WHITE)
    canvas_obj.setFont('Helvetica-Bold', 52)
    canvas_obj.drawCentredString(w/2, h - 150, 'Academic')
    canvas_obj.setFillColor(ACCENT)
    canvas_obj.setFont('Helvetica-Bold', 52)
    canvas_obj.drawCentredString(w/2, h - 210, 'Assistant')

    # Subtitle
    canvas_obj.setFillColor(HexColor('#D1D5DB'))
    canvas_obj.setFont('Helvetica', 16)
    canvas_obj.drawCentredString(w/2, h - 250, 'Plateforme Academique Decentralisee')

    # Separator
    canvas_obj.setStrokeColor(ACCENT)
    canvas_obj.setLineWidth(2)
    canvas_obj.line(80, h - 275, w - 80, h - 275)

    # Report type
    canvas_obj.setFillColor(WHITE)
    canvas_obj.setFont('Helvetica-Bold', 20)
    canvas_obj.drawCentredString(w/2, h - 310, 'Rapport Technique du Projet Final')
    canvas_obj.setFillColor(HexColor('#9CA3AF'))
    canvas_obj.setFont('Helvetica', 13)
    canvas_obj.drawCentredString(w/2, h - 335, 'Blockchain  \xb7  Smart Contracts  \xb7  Intelligence Artificielle')

    # Hex decorations
    canvas_obj.setStrokeColor(HexColor('#374151'))
    canvas_obj.setLineWidth(1)
    for i in range(5):
        r = 60 + i * 25
        canvas_obj.circle(w/2, h/2 - 20, r, fill=0, stroke=1)

    # Tech badges
    badges = ['Hardhat', 'Solidity', 'Node.js', 'Claude AI', 'viem']
    bx = 80
    canvas_obj.setFillColor(HexColor('#111827'))
    canvas_obj.setStrokeColor(ACCENT)
    canvas_obj.setLineWidth(1)
    for b in badges:
        bw = 80
        canvas_obj.roundRect(bx, h/2 - 75, bw, 24, 4, fill=1, stroke=1)
        canvas_obj.setFillColor(ACCENT)
        canvas_obj.setFont('Helvetica-Bold', 9)
        canvas_obj.drawCentredString(bx + bw/2, h/2 - 65, b)
        canvas_obj.setFillColor(HexColor('#111827'))
        bx += 92

    # Info table
    info = [
        ('Institution :', 'Universite Euromed de Fes (UEMF)'),
        ('Technologie :', 'Hardhat + viem + Claude API'),
        ('Reseau :', 'Ethereum (Hardhat local Node)'),
        ('Date :', 'Juin 2026'),
    ]
    canvas_obj.setFont('Helvetica-Bold', 10)
    canvas_obj.setFillColor(GOLD)
    y_info = h/2 - 140
    for label, val in info:
        canvas_obj.setFillColor(GOLD)
        canvas_obj.setFont('Helvetica-Bold', 10)
        canvas_obj.drawString(100, y_info, label)
        canvas_obj.setFillColor(WHITE)
        canvas_obj.setFont('Helvetica', 10)
        canvas_obj.drawString(230, y_info, val)
        y_info -= 22

    canvas_obj.restoreState()


def header_footer(canvas_obj, doc):
    canvas_obj.saveState()
    w = PAGE_W
    # Header
    canvas_obj.setFillColor(PRIMARY)
    canvas_obj.setFont('Helvetica-Bold', 9)
    canvas_obj.drawString(2*cm, PAGE_H - 1.5*cm, 'Academic Assistant')
    canvas_obj.setFillColor(ACCENT)
    canvas_obj.setFont('Helvetica', 9)
    canvas_obj.drawRightString(w - 2*cm, PAGE_H - 1.5*cm, 'Blockchain + IA')
    canvas_obj.setStrokeColor(ACCENT)
    canvas_obj.setLineWidth(0.5)
    canvas_obj.line(2*cm, PAGE_H - 1.8*cm, w - 2*cm, PAGE_H - 1.8*cm)
    # Footer
    canvas_obj.setFillColor(GRAY)
    canvas_obj.setFont('Helvetica', 8)
    canvas_obj.drawCentredString(w/2, 1.2*cm, f'{doc.page}')
    canvas_obj.line(2*cm, 1.6*cm, w - 2*cm, 1.6*cm)
    canvas_obj.restoreState()


# ─── Styles ───────────────────────────────────────────────────────────────────
styles = getSampleStyleSheet()

h1 = ParagraphStyle('H1', parent=styles['Heading1'],
    textColor=PRIMARY, fontSize=22, spaceAfter=8, spaceBefore=20,
    fontName='Helvetica-Bold')
h2 = ParagraphStyle('H2', parent=styles['Heading2'],
    textColor=PRIMARY, fontSize=16, spaceAfter=6, spaceBefore=14,
    fontName='Helvetica-Bold', borderPad=0)
h3 = ParagraphStyle('H3', parent=styles['Heading3'],
    textColor=ACCENT, fontSize=13, spaceAfter=5, spaceBefore=10,
    fontName='Helvetica-Bold')
body = ParagraphStyle('Body', parent=styles['Normal'],
    fontSize=10, leading=15, textColor=PRIMARY, spaceAfter=6,
    alignment=TA_JUSTIFY, fontName='Helvetica')
bullet_style = ParagraphStyle('Bullet', parent=body,
    leftIndent=15, bulletIndent=0, spaceAfter=4)
caption_style = ParagraphStyle('Caption', parent=body,
    fontSize=9, textColor=GRAY, alignment=TA_CENTER, italic=True, spaceAfter=12)
toc_style = ParagraphStyle('TOC', parent=body, fontSize=11, leading=18)


def hr(): return HRFlowable(width='100%', thickness=0.5, color=ACCENT, spaceAfter=8, spaceBefore=8)
def sp(n=8): return Spacer(1, n)
def p(text, style=body): return Paragraph(text, style)
def h1_(t): return Paragraph(t, h1)
def h2_(t): return Paragraph(t, h2)
def h3_(t): return Paragraph(t, h3)


def section_title(number, title):
    return [
        sp(16),
        Paragraph(f'<font color="#3B82F6">{number}</font>  {title}',
                  ParagraphStyle('ST', parent=h1, fontSize=18, spaceBefore=0)),
        HRFlowable(width='100%', thickness=2, color=ACCENT, spaceAfter=10),
    ]


def subsection_title(number, title):
    return [
        sp(10),
        Paragraph(f'<font color="#3B82F6">{number}</font>  {title}',
                  ParagraphStyle('SS', parent=h2, fontSize=14, spaceBefore=0)),
        HRFlowable(width='100%', thickness=0.5, color=HexColor('#D1D5DB'), spaceAfter=6),
    ]


def api_table(rows, col_widths=None):
    if col_widths is None:
        col_widths = [2.5*cm, 5.5*cm, 9*cm]
    t = Table(rows, colWidths=col_widths)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY),
        ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, LIGHT_ACCENT]),
        ('FONTNAME', (0, 1), (-1, -1), 'Courier'),
        ('FONTSIZE', (0, 1), (-1, -1), 8.5),
        ('GRID', (0, 0), (-1, -1), 0.3, HexColor('#D1D5DB')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('ROWBACKGROUNDS', (0, 0), (-1, 0), [PRIMARY]),
    ]))
    return t


def img_placeholder(title, height=5*cm):
    """Generate a placeholder box for screenshots."""
    t = Table([
        [Paragraph(f'<font color="#6B7280"><i>[Screenshot : {title}]</i></font>',
                   ParagraphStyle('ph', parent=body, fontSize=9, alignment=TA_CENTER))]
    ], colWidths=[PAGE_W - 4*cm], rowHeights=[height])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), HexColor('#F9FAFB')),
        ('BOX', (0, 0), (-1, -1), 1, HexColor('#D1D5DB')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ]))
    return t


# ─── Build story ─────────────────────────────────────────────────────────────
story = []

# ── TOC (manual) ──────────────────────────────────────────────────────────────
story.append(PageBreak())  # cover is page 1, TOC starts page 2
story.append(p('<b>Table des Matieres</b>',
    ParagraphStyle('TOCH', parent=h1, fontSize=22, spaceBefore=30)))
story.append(hr())
story.append(sp(12))

toc_entries = [
    ('1', 'Introduction et Vue d\'Ensemble', '3'),
    ('  1.1', 'Presentation du Projet', '3'),
    ('  1.2', 'Stack Technique', '3'),
    ('2', 'Fonctionnalites', '4'),
    ('  2.1', 'Interface Professeur', '4'),
    ('  2.2', 'Interface Etudiant', '6'),
    ('3', 'Architecture du Systeme', '9'),
    ('  3.1', 'Vue d\'Ensemble', '9'),
    ('  3.2', 'Structure des Fichiers', '9'),
    ('4', 'Smart Contracts', '11'),
    ('  4.1', 'AcademicAnnouncements.sol', '11'),
    ('  4.2', 'DocumentRegistry.sol', '13'),
    ('5', 'Backend API', '15'),
    ('  5.1', 'Architecture Express', '15'),
    ('  5.2', 'Endpoints API', '15'),
    ('  5.3', 'Service IA (Claude API)', '17'),
    ('6', 'Comptes Hardhat', '19'),
    ('7', 'Installation et Demarrage', '21'),
    ('  7.1', 'Prerequis', '21'),
    ('  7.2', 'Installation Initiale', '21'),
    ('  7.3', 'Lancement (3 Terminaux)', '22'),
    ('  7.4', 'Test de l\'API', '23'),
    ('8', 'Workflows Utilisateur', '24'),
    ('9', 'Conclusion', '26'),
]

for num, title, page in toc_entries:
    bold = 'b' if not num.startswith('  ') else ''
    indent = 0 if not num.startswith('  ') else 20
    row = Table(
        [[Paragraph(f'<{bold}>{num}  {title}</{bold}>' if bold else f'{num}  {title}',
                    ParagraphStyle('ti', parent=body, leftIndent=indent, fontSize=10 if not bold else 11)),
          Paragraph(f'<{bold}>{page}</{bold}>' if bold else page,
                    ParagraphStyle('tp', parent=body, alignment=TA_RIGHT, fontSize=10 if not bold else 11))]],
        colWidths=[PAGE_W - 5*cm, 1.5*cm]
    )
    row.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))
    story.append(row)
    if not num.startswith('  '):
        story.append(HRFlowable(width='100%', thickness=0.3, color=HexColor('#E5E7EB'), spaceAfter=2))

# ══════════════════════════════════════════════════════════════════════════════
# CHAPTER 1 — INTRODUCTION
# ══════════════════════════════════════════════════════════════════════════════
story.append(PageBreak())
story += section_title('1', 'Introduction et Vue d\'Ensemble')

story.append(p('''<b>Academic Assistant</b> est une application web full-stack qui combine la technologie
<b>blockchain Ethereum</b> et l\'<b>intelligence artificielle</b> pour moderniser la communication
academique universitaire. Elle offre une plateforme ou les professeurs peuvent publier des
annonces de cours de maniere immuable et verifiable on-chain, et ou les etudiants peuvent
interroger un assistant IA contextuel base sur ces memes donnees blockchain.'''))

story.append(sp(10))
story.append(FeatureBox('Proposition de valeur du projet', [
    'Immutabilite : annonces horodatees et non modifiables on-chain',
    'Verification documentaire : hash SHA-256 des fichiers pedagogiques sur blockchain',
    'Assistant IA : chatbot Claude AI contextualise par les annonces blockchain',
    'Deux interfaces : sombre (Professeur) et claire (Etudiant)',
    'Architecture decentralisee : aucun intermediaire de confiance necessaire',
]))
story.append(sp(16))

story += subsection_title('1.1', 'Presentation du Projet')
story.append(p('''Le projet adresse une problematique concrete de l\'environnement universitaire :
la communication des informations de cours (TDs, CMs, examens) est souvent informelle,
non tracable, et facilement falsifiable. Academic Assistant resout ce probleme en gravant
toutes les annonces sur une blockchain Ethereum locale, garantissant ainsi leur authenticite,
leur horodatage precis, et leur immutabilite.'''))

story.append(sp(12))
story += subsection_title('1.2', 'Stack Technique')

stack_data = [
    [Paragraph('<b>Couche</b>', ParagraphStyle('th', parent=body, textColor=WHITE, fontSize=9, fontName='Helvetica-Bold')),
     Paragraph('<b>Technologies</b>', ParagraphStyle('th', parent=body, textColor=WHITE, fontSize=9, fontName='Helvetica-Bold'))],
    ['Smart Contracts', 'Solidity 0.8+, Hardhat, ethers.js'],
    ['Reseau local', 'Hardhat Node (20 comptes, 10 000 ETH chacun)'],
    ['Backend API', 'Node.js, Express, TypeScript, viem, Anthropic Claude API'],
    ['Frontend Etudiant', 'HTML/CSS/JS vanilla, theme clair, viem (direct blockchain calls)'],
    ['Frontend Professeur', 'HTML/CSS/JS vanilla, theme sombre, viem'],
    ['Hachage documentaire', 'Web Crypto API (SHA-256, calcule cote navigateur)'],
]
t = Table(stack_data, colWidths=[5*cm, 12*cm])
t.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), PRIMARY),
    ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, LIGHT_ACCENT]),
    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
    ('FONTSIZE', (0, 1), (-1, -1), 9),
    ('GRID', (0, 0), (-1, -1), 0.3, HexColor('#D1D5DB')),
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ('TOPPADDING', (0, 0), (-1, -1), 6),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ('LEFTPADDING', (0, 0), (-1, -1), 10),
]))
story.append(t)

# ══════════════════════════════════════════════════════════════════════════════
# CHAPTER 2 — FEATURES
# ══════════════════════════════════════════════════════════════════════════════
story.append(PageBreak())
story += section_title('2', 'Fonctionnalites')

story += subsection_title('2.1', 'Interface Professeur')
story.append(p('''L\'interface professeur est concue en <b>theme sombre</b> (fond <code>#0F0F1A</code>).
Elle propose trois fonctionnalites principales accessibles via la barre de navigation :
Publier, Documents, Annonces.'''))
story.append(sp(10))

# 2.1.1 Publish
story.append(p('<b>2.1.1 Publication d\'Annonces (On-chain)</b>', h3))
story.append(img_placeholder('Interface de publication d\'annonce — Professeur (theme sombre)', 4.5*cm))
story.append(p('Figure 1 : Nouvelle Annonce — formulaire de publication on-chain (Interface Professeur)', caption_style))
story.append(sp(8))
story.append(p('''Le professeur remplit un formulaire comprenant :'''))
bullets = [
    '<b>Contenu</b> : texte de l\'annonce (maximum 32 octets, format <font name="Courier">bytes32</font> on-chain)',
    '<b>Categorie</b> : TD, CM, TP, Examen, ou autre',
    '<b>Groupe cible</b> : MF1, MF2, GI1, GI2, etc.',
    '<b>Compte (index)</b> : index du compte Hardhat qui signera la transaction (0 a 19)',
]
for b in bullets:
    story.append(Paragraph(f'<bullet>\u2022</bullet> {b}', bullet_style))
story.append(sp(8))
story.append(p('''En cliquant sur <b>"Publier on-chain"</b>, une transaction Ethereum est signee par
le compte choisi et envoyee au smart contract <font name="Courier">AcademicAnnouncements</font>.
L\'annonce est alors gravee de facon permanente, avec un horodatage blockchain exact.'''))

story.append(sp(16))

# 2.1.2 Documents
story.append(p('<b>2.1.2 Depot de Documents (Hash SHA-256)</b>', h3))
story.append(img_placeholder('Interface de depot de document — Professeur (theme sombre)', 4.5*cm))
story.append(p('Figure 2 : Deposer un Document — enregistrement du hash SHA-256 on-chain (Professeur)', caption_style))
story.append(sp(8))
story.append(p('''Le professeur peut deposer n\'importe quel fichier pedagogique (PDF, DOCX, etc.).
L\'application calcule le <b>hash SHA-256</b> du fichier entierement cote navigateur
(via la Web Crypto API), puis enregistre ce hash dans le smart contract
<font name="Courier">DocumentRegistry</font>. Ce hash servira de preuve d\'integrite
verifiable par les etudiants sans jamais uploader le fichier lui-meme.'''))

# ── Student interface ──────────────────────────────────────────────────────────
story.append(PageBreak())
story += subsection_title('2.2', 'Interface Etudiant')
story.append(p('''L\'interface etudiant adopte un <b>theme clair</b> (fond <font name="Courier">#F3F0E8</font>)
avec une typographie moderne. L\'adresse du compte etudiant connecte est affichee dans la
barre de navigation (ex : <font name="Courier">0x3c44...93bc</font>).'''))
story.append(sp(12))

# Announcements
story.append(p('<b>2.2.1 Annonces de Cours</b>', h3))
story.append(img_placeholder('Liste des annonces de cours — Etudiant', 4.5*cm))
story.append(p('Figure 3 : Annonces de cours filtrees par groupe MF1 — Interface Etudiant', caption_style))
story.append(sp(8))
story.append(p('''L\'onglet "Annonces" affiche toutes les annonces publiees on-chain pour le groupe
de l\'etudiant. Chaque annonce indique :'''))
bullets2 = [
    'Son <b>identifiant numerique</b> (#1, #2, ...) et son <b>hash de transaction</b> complet',
    'Ses <b>tags de categorie</b> (ex : TD) et de <b>groupe cible</b> (ex : MF1)',
    'Son <b>horodatage blockchain</b> exact (ex : 11/06/2026 22:22:42)',
    'Un bouton de <b>marquage "Lu"</b> (etat local persistant)',
]
for b in bullets2:
    story.append(Paragraph(f'<bullet>\u2022</bullet> {b}', bullet_style))
story.append(sp(8))
story.append(p('''Un champ de filtre par groupe permet de n\'afficher que les annonces pertinentes.
Un bouton de rafraichissement permet de recharger les donnees depuis la blockchain.'''))
story.append(sp(16))

# Verify doc
story.append(p('<b>2.2.2 Verification de Document</b>', h3))
story.append(img_placeholder('Verification de document — Interface Etudiant', 4.5*cm))
story.append(p('Figure 4 : Verifier un Document — integrite verifiee via blockchain (Etudiant)', caption_style))
story.append(sp(8))
story.append(p('''L\'onglet "Verifier doc" permet a l\'etudiant de verifier l\'authenticite d\'un
document pedagogique en trois etapes automatiques :'''))
steps = [
    'L\'etudiant glisse-depose le fichier a verifier dans la zone de depot',
    'L\'application calcule le <b>SHA-256</b> du fichier cote navigateur',
    'Le hash est compare contre le smart contract <font name="Courier">DocumentRegistry</font> en lecture seule',
]
for i, s in enumerate(steps, 1):
    story.append(Paragraph(f'<b>{i}.</b> {s}', bullet_style))
story.append(sp(8))
story.append(p('''Le resultat indique clairement si le hash est <b>enregistre on-chain</b> (document
authentique, non modifie) ou <b>absent du registre</b> (document inconnu ou altere).
L\'operation est entierement gratuite (appel <font name="Courier">view</font> sans transaction).'''))

story.append(sp(16))

# AI Assistant
story.append(p('<b>2.2.3 Assistant IA (Chatbot contextuel)</b>', h3))
story.append(img_placeholder('Assistant IA — Chat contextuel avec annonces blockchain', 5*cm))
story.append(p('Figure 5 : Assistant IA repondant aux questions des etudiants via contexte on-chain', caption_style))
story.append(sp(8))
story.append(p('''L\'assistant IA est la fonctionnalite la plus avancee du projet. Il fonctionne selon
un principe de <b>RAG (Retrieval-Augmented Generation)</b> base sur la blockchain :'''))
steps2 = [
    "L'etudiant saisit une question dans le champ (ex : <i>\"DONNE MOI LES DETAIL SU LE TD\"</i>)",
    "Le backend recupere toutes les annonces on-chain pour le groupe de l'etudiant (MF1)",
    "Ces annonces sont injectees comme <b>contexte</b> dans le prompt envoye a l'<b>API Claude</b>",
    "Claude genere une reponse precise (ex : <i>\"TD demain a 15h30 pour le groupe MF1\"</i>)",
]
for i, s in enumerate(steps2, 1):
    story.append(Paragraph(f'<b>{i}.</b> {s}', bullet_style))
story.append(sp(10))
story.append(NoteBox(
    'L\'assistant opere en RAG pur : il ne genere aucune information ex nihilo, mais se base exclusivement '
    'sur les donnees blockchain verifiees et immuables. Cela garantit des reponses fiables et traçables.'
))

# ══════════════════════════════════════════════════════════════════════════════
# CHAPTER 3 — ARCHITECTURE
# ══════════════════════════════════════════════════════════════════════════════
story.append(PageBreak())
story += section_title('3', 'Architecture du Systeme')

story += subsection_title('3.1', 'Vue d\'Ensemble')
story.append(p('''Le systeme est compose de cinq couches distinctes communiquant entre elles :'''))
arch_data = [
    [Paragraph('<b>Composant</b>', ParagraphStyle('th2', parent=body, textColor=WHITE, fontSize=9, fontName='Helvetica-Bold')),
     Paragraph('<b>Technologie</b>', ParagraphStyle('th2', parent=body, textColor=WHITE, fontSize=9, fontName='Helvetica-Bold')),
     Paragraph('<b>Port / URL</b>', ParagraphStyle('th2', parent=body, textColor=WHITE, fontSize=9, fontName='Helvetica-Bold')),
     Paragraph('<b>Role</b>', ParagraphStyle('th2', parent=body, textColor=WHITE, fontSize=9, fontName='Helvetica-Bold'))],
    ['Frontend Etudiant', 'HTML/CSS/JS', 'localhost:3000', 'UI consultation + IA'],
    ['Frontend Professeur', 'HTML/CSS/JS', 'localhost:3000', 'UI publication + depot'],
    ['Backend API', 'Node.js + Express', 'localhost:3001', 'Logique metier + Claude'],
    ['Blockchain RPC', 'Hardhat Node', '127.0.0.1:8545', 'Ethereum local'],
    ['IA API', 'Anthropic Claude', 'api.anthropic.com', 'LLM contextuel'],
]
t = Table(arch_data, colWidths=[4*cm, 3.5*cm, 3.5*cm, 6*cm])
t.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), PRIMARY),
    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, LIGHT_ACCENT]),
    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
    ('FONTSIZE', (0, 1), (-1, -1), 9),
    ('GRID', (0, 0), (-1, -1), 0.3, HexColor('#D1D5DB')),
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ('TOPPADDING', (0, 0), (-1, -1), 6),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ('LEFTPADDING', (0, 0), (-1, -1), 8),
]))
story.append(t)
story.append(sp(12))

story += subsection_title('3.2', 'Structure des Fichiers du Projet')
story.append(CodeBlock(
    'final-project/\n'
    '|-- contracts/\n'
    '|   |-- AcademicAnnouncements.sol   # Smart contract annonces\n'
    '|   `-- DocumentRegistry.sol        # Smart contract documents\n'
    '|-- scripts/\n'
    '|   |-- deploy.js                   # Deploiement Hardhat\n'
    '|   `-- api_test.js                 # Tests automatises API\n'
    '|-- test/\n'
    '|   `-- AcademicAnnouncements.test.js\n'
    '|-- backend/\n'
    '|   |-- src/\n'
    '|   |   |-- index.ts                # Point dentree Express\n'
    '|   |   |-- routes/\n'
    '|   |   |   |-- announcements.ts    # Routes annonces\n'
    '|   |   |   |-- documents.ts        # Routes documents\n'
    '|   |   |   `-- ai.ts               # Routes assistant IA\n'
    '|   |   `-- services/\n'
    '|   |       |-- blockchain.ts       # Interactions viem\n'
    '|   |       `-- ai.ts               # Service Claude API\n'
    '|   |-- package.json\n'
    '|   `-- tsconfig.json\n'
    '|-- frontend/\n'
    '|   |-- index.html                  # Interface etudiant\n'
    '|   |-- professor.html              # Interface professeur\n'
    '|   |-- css/\n'
    '|   `-- js/\n'
    '|-- hardhat.config.js\n'
    '`-- package.json'
))

# ══════════════════════════════════════════════════════════════════════════════
# CHAPTER 4 — SMART CONTRACTS
# ══════════════════════════════════════════════════════════════════════════════
story.append(PageBreak())
story += section_title('4', 'Smart Contracts')

story += subsection_title('4.1', 'AcademicAnnouncements.sol')
story.append(p('''Ce contrat Solidity gere la publication et la recuperation des annonces academiques.
Il stocke chaque annonce sous forme d\'une struct contenant son contenu (encode en
<font name="Courier">bytes32</font>), sa categorie, son groupe cible, l\'adresse de l\'auteur,
et le timestamp blockchain.'''))
story.append(sp(8))

story.append(CodeBlock(
    '// SPDX-License-Identifier: MIT\n'
    'pragma solidity ^0.8.0;\n'
    '\n'
    'contract AcademicAnnouncements {\n'
    '\n'
    '    struct Announcement {\n'
    '        bytes32 content;      // Contenu (max 32 octets)\n'
    '        bytes32 category;     // Categorie : TD, CM, TP, Examen...\n'
    '        bytes32 targetGroup;  // Groupe cible : MF1, MF2, GI1...\n'
    '        address author;       // Adresse Ethereum du professeur\n'
    '        uint256 timestamp;    // Horodatage unix (block.timestamp)\n'
    '    }\n'
    '\n'
    '    Announcement[] public announcements;\n'
    '\n'
    '    event AnnouncementPublished(\n'
    '        uint256 indexed id,\n'
    '        address indexed author,\n'
    '        bytes32 targetGroup,\n'
    '        uint256 timestamp\n'
    '    );\n'
    '\n'
    '    // Publie une nouvelle annonce on-chain\n'
    '    function publishAnnouncement(\n'
    '        bytes32 content,\n'
    '        bytes32 category,\n'
    '        bytes32 targetGroup\n'
    '    ) external returns (uint256) {\n'
    '        announcements.push(Announcement({\n'
    '            content: content,\n'
    '            category: category,\n'
    '            targetGroup: targetGroup,\n'
    '            author: msg.sender,\n'
    '            timestamp: block.timestamp\n'
    '        }));\n'
    '        uint256 id = announcements.length - 1;\n'
    '        emit AnnouncementPublished(id, msg.sender, targetGroup, block.timestamp);\n'
    '        return id;\n'
    '    }\n'
    '\n'
    '    // Retourne toutes les annonces d\'un groupe specifique\n'
    '    function getAnnouncementsForGroup(bytes32 group)\n'
    '        external view returns (Announcement[] memory)\n'
    '    {\n'
    '        uint256 count = 0;\n'
    '        for (uint i = 0; i < announcements.length; i++) {\n'
    '            if (announcements[i].targetGroup == group) count++;\n'
    '        }\n'
    '        Announcement[] memory result = new Announcement[](count);\n'
    '        uint256 j = 0;\n'
    '        for (uint i = 0; i < announcements.length; i++) {\n'
    '            if (announcements[i].targetGroup == group)\n'
    '                result[j++] = announcements[i];\n'
    '        }\n'
    '        return result;\n'
    '    }\n'
    '\n'
    '    function getTotalAnnouncements() external view returns (uint256) {\n'
    '        return announcements.length;\n'
    '    }\n'
    '}'
))
story.append(sp(12))

story.append(p('<b>Fonctions principales :</b>'))
funcs_data = [
    [Paragraph('<b>Fonction</b>', ParagraphStyle('th3', parent=body, textColor=WHITE, fontSize=9, fontName='Helvetica-Bold')),
     Paragraph('<b>Type</b>', ParagraphStyle('th3', parent=body, textColor=WHITE, fontSize=9, fontName='Helvetica-Bold')),
     Paragraph('<b>Description</b>', ParagraphStyle('th3', parent=body, textColor=WHITE, fontSize=9, fontName='Helvetica-Bold'))],
    ['publishAnnouncement()', 'write (gaz)', 'Publie une annonce on-chain, emets un event'],
    ['getAnnouncementsForGroup()', 'view (gratuit)', 'Recupere les annonces filtrees par groupe'],
    ['getTotalAnnouncements()', 'view (gratuit)', 'Retourne le nombre total d\'annonces'],
]
story.append(api_table(funcs_data, [5.5*cm, 3.5*cm, 8*cm]))

story.append(sp(20))
story += subsection_title('4.2', 'DocumentRegistry.sol')
story.append(p('''Ce contrat maintient un registre immuable des hash SHA-256 de fichiers pedagogiques.
Il utilise un <font name="Courier">mapping</font> pour un acces en O(1) a chaque hash.'''))
story.append(sp(8))

story.append(CodeBlock(
    '// SPDX-License-Identifier: MIT\n'
    'pragma solidity ^0.8.0;\n'
    '\n'
    'contract DocumentRegistry {\n'
    '\n'
    '    struct Document {\n'
    '        bytes32 fileHash;      // Hash SHA-256 du fichier\n'
    '        bytes32 targetGroup;   // Groupe concerne\n'
    '        address uploader;      // Adresse du professeur\n'
    '        uint256 timestamp;     // Date d\'enregistrement\n'
    '    }\n'
    '\n'
    '    mapping(bytes32 => Document) public documents;\n'
    '    bytes32[] public documentHashes;\n'
    '\n'
    '    event DocumentRegistered(\n'
    '        bytes32 indexed fileHash,\n'
    '        address indexed uploader,\n'
    '        bytes32 targetGroup,\n'
    '        uint256 timestamp\n'
    '    );\n'
    '\n'
    '    function registerDocument(bytes32 fileHash, bytes32 targetGroup) external {\n'
    '        require(documents[fileHash].timestamp == 0, "Already registered");\n'
    '        documents[fileHash] = Document({\n'
    '            fileHash: fileHash,\n'
    '            targetGroup: targetGroup,\n'
    '            uploader: msg.sender,\n'
    '            timestamp: block.timestamp\n'
    '        });\n'
    '        documentHashes.push(fileHash);\n'
    '        emit DocumentRegistered(fileHash, msg.sender, targetGroup, block.timestamp);\n'
    '    }\n'
    '\n'
    '    // Retourne (existe, timestamp, uploadeur)\n'
    '    function verifyDocument(bytes32 fileHash)\n'
    '        external view\n'
    '        returns (bool exists, uint256 timestamp, address uploader)\n'
    '    {\n'
    '        Document memory doc = documents[fileHash];\n'
    '        return (doc.timestamp != 0, doc.timestamp, doc.uploader);\n'
    '    }\n'
    '}'
))

# ══════════════════════════════════════════════════════════════════════════════
# CHAPTER 5 — BACKEND API
# ══════════════════════════════════════════════════════════════════════════════
story.append(PageBreak())
story += section_title('5', 'Backend API')

story += subsection_title('5.1', 'Architecture Express')
story.append(p('''Le backend est developpe en <b>TypeScript</b> avec <b>Express.js</b>.
Il est le point central du systeme : il connecte les frontends a la blockchain via
<b>viem</b> et a l\'IA via l\'<b>API Anthropic Claude</b>.'''))
story.append(sp(8))
story.append(CodeBlock('Base URL : http://localhost:3001\nContent-Type : application/json'))
story.append(sp(12))

story += subsection_title('5.2', 'Endpoints API')

# Annonces endpoints
story.append(p('<b>5.2.1 Annonces</b>', h3))
ann_data = [
    [Paragraph('<b>Methode</b>', ParagraphStyle('th4', parent=body, textColor=WHITE, fontSize=9, fontName='Helvetica-Bold')),
     Paragraph('<b>Endpoint</b>', ParagraphStyle('th4', parent=body, textColor=WHITE, fontSize=9, fontName='Helvetica-Bold')),
     Paragraph('<b>Description</b>', ParagraphStyle('th4', parent=body, textColor=WHITE, fontSize=9, fontName='Helvetica-Bold'))],
    ['GET', '/api/announcements', 'Recupere toutes les annonces on-chain'],
    ['GET', '/api/announcements?group=MF1', 'Filtre par groupe (ex : MF1)'],
    ['POST', '/api/announcements', 'Publie une nouvelle annonce on-chain'],
    ['GET', '/api/announcements/:id', 'Recupere une annonce par son ID'],
]
story.append(api_table(ann_data, [2*cm, 6*cm, 9*cm]))
story.append(sp(12))

story.append(p('<b>Exemple de corps POST /api/announcements :</b>'))
story.append(CodeBlock(
    '{\n'
    '  "content":      "TD demain 15h30 salle A204",\n'
    '  "category":     "TD",\n'
    '  "targetGroup":  "MF1",\n'
    '  "accountIndex": 1\n'
    '}'
))
story.append(sp(12))

# Documents endpoints
story.append(p('<b>5.2.2 Documents</b>', h3))
doc_data = [
    [Paragraph('<b>Methode</b>', ParagraphStyle('th5', parent=body, textColor=WHITE, fontSize=9, fontName='Helvetica-Bold')),
     Paragraph('<b>Endpoint</b>', ParagraphStyle('th5', parent=body, textColor=WHITE, fontSize=9, fontName='Helvetica-Bold')),
     Paragraph('<b>Description</b>', ParagraphStyle('th5', parent=body, textColor=WHITE, fontSize=9, fontName='Helvetica-Bold'))],
    ['POST', '/api/documents/register', 'Enregistre un hash SHA-256 on-chain'],
    ['GET', '/api/documents/verify/:hash', 'Verifie si un hash est dans le registre'],
    ['GET', '/api/documents', 'Liste tous les documents enregistres'],
]
story.append(api_table(doc_data, [2*cm, 6*cm, 9*cm]))
story.append(sp(12))

# IA endpoint
story.append(p('<b>5.2.3 Assistant IA</b>', h3))
ai_data = [
    [Paragraph('<b>Methode</b>', ParagraphStyle('th6', parent=body, textColor=WHITE, fontSize=9, fontName='Helvetica-Bold')),
     Paragraph('<b>Endpoint</b>', ParagraphStyle('th6', parent=body, textColor=WHITE, fontSize=9, fontName='Helvetica-Bold')),
     Paragraph('<b>Description</b>', ParagraphStyle('th6', parent=body, textColor=WHITE, fontSize=9, fontName='Helvetica-Bold'))],
    ['POST', '/api/ai/chat', 'Envoie une question a l\'assistant IA contextuel'],
]
story.append(api_table(ai_data, [2*cm, 6*cm, 9*cm]))
story.append(sp(12))

story.append(p('<b>Exemple de requete :</b>'))
story.append(CodeBlock(
    'POST /api/ai/chat\n'
    '{\n'
    '  "question": "Y a-t-il un TD demain pour MF1 ?",\n'
    '  "group":    "MF1"\n'
    '}'
))
story.append(sp(8))
story.append(p('<b>Exemple de reponse :</b>'))
story.append(CodeBlock(
    '{\n'
    '  "answer": "D\'apres les annonces, il y a bien un TD prevu :\\n'
    '             Demain a 15h30 pour le groupe MF1.",\n'
    '  "context_used": 1,\n'
    '  "timestamp": "2026-06-11T22:24:04.000Z"\n'
    '}'
))

story.append(sp(16))
story += subsection_title('5.3', 'Service IA (Claude API)')
story.append(p('''Le service IA est le coeur intelligent du backend. Il recupere le contexte
blockchain (annonces du groupe) et l\'injecte dans le prompt envoye a Claude :'''))
story.append(sp(8))

story.append(CodeBlock(
    'import Anthropic from "@anthropic-ai/sdk";\n'
    '\n'
    'const client = new Anthropic(); // Lit ANTHROPIC_API_KEY automatiquement\n'
    '\n'
    'export async function askWithContext(\n'
    '  question: string,\n'
    '  announcements: Announcement[]\n'
    '): Promise<string> {\n'
    '\n'
    '  // 1. Construire le contexte depuis les annonces blockchain\n'
    '  const context = announcements\n'
    '    .map(a => `[${a.category}] ${a.content} (Groupe: ${a.targetGroup})`)\n'
    '    .join("\\n");\n'
    '\n'
    '  // 2. Appeler l\'API Claude avec contexte injecte\n'
    '  const response = await client.messages.create({\n'
    '    model: "claude-opus-4-6",\n'
    '    max_tokens: 512,\n'
    '    system: `Tu es un assistant academique universitaire.\n'
    '             Reponds uniquement en te basant sur les annonces fournies.\n'
    '             Si l\'information est absente, dis-le clairement.`,\n'
    '    messages: [{\n'
    '      role: "user",\n'
    '      content: `Contexte des annonces:\\n${context}\\n\\nQuestion: ${question}`\n'
    '    }]\n'
    '  });\n'
    '\n'
    '  return response.content[0].type === "text"\n'
    '    ? response.content[0].text\n'
    '    : "Reponse non disponible.";\n'
    '}'
))

# ══════════════════════════════════════════════════════════════════════════════
# CHAPTER 6 — HARDHAT ACCOUNTS
# ══════════════════════════════════════════════════════════════════════════════
story.append(PageBreak())
story += section_title('6', 'Comptes Hardhat')

story.append(p('''Hardhat genere automatiquement <b>20 comptes de test deterministes</b>, chacun dote de
<b>10 000 ETH</b> (faux ETH de test). Ces comptes sont affiches au demarrage du noeud
(<font name="Courier">npx hardhat node</font>) avec leurs adresses et cles privees.'''))
story.append(sp(12))

story.append(img_placeholder('Terminal Hardhat — Comptes #0 a #9 avec cles privees', 5*cm))
story.append(p('Figure 6 : Comptes Hardhat #0 a #9 — affiches au demarrage du noeud local', caption_style))
story.append(sp(10))

story.append(img_placeholder('Terminal Hardhat — Comptes #8 a #19 (suite)', 5*cm))
story.append(p('Figure 7 : Comptes Hardhat #8 a #19 — suite des comptes de test', caption_style))
story.append(sp(12))

story.append(NoteBox(
    'SECURITE : Ces comptes et leurs cles privees sont publiquement connus. '
    'Tout fonds envoye sur Mainnet ou un reseau live sera perdu. '
    'Ils sont exclusivement destines au developpement local.'
))
story.append(sp(12))

story.append(p('<b>Roles des comptes dans l\'application :</b>'))
accounts_data = [
    [Paragraph('<b>Compte</b>', ParagraphStyle('th7', parent=body, textColor=WHITE, fontSize=9, fontName='Helvetica-Bold')),
     Paragraph('<b>Adresse</b>', ParagraphStyle('th7', parent=body, textColor=WHITE, fontSize=9, fontName='Helvetica-Bold')),
     Paragraph('<b>Role</b>', ParagraphStyle('th7', parent=body, textColor=WHITE, fontSize=9, fontName='Helvetica-Bold'))],
    ['#0', '0xf39Fd6e51aad88F6F4ce6aB88827279cffFb92266', 'Deployeur des smart contracts'],
    ['#1', '0x70997970C51812dc3A010C7d01b50e0d17dc79C8', 'Professeur par defaut (index 1)'],
    ['#2', '0x3C44CdDdB6a900Fa2b585dd299e03d12FA4293BC', 'Etudiant connecte par defaut'],
    ['#3-19', '...', 'Professeurs/etudiants additionnels pour les tests'],
]
t = Table(accounts_data, colWidths=[2*cm, 8.5*cm, 6.5*cm])
t.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), PRIMARY),
    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, LIGHT_ACCENT]),
    ('FONTNAME', (0, 1), (-1, -1), 'Courier'),
    ('FONTSIZE', (0, 1), (-1, -1), 7.5),
    ('GRID', (0, 0), (-1, -1), 0.3, HexColor('#D1D5DB')),
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ('TOPPADDING', (0, 0), (-1, -1), 5),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ('LEFTPADDING', (0, 0), (-1, -1), 8),
]))
story.append(t)
story.append(p('''Dans les formulaires, le champ <b>"Compte (index)"</b> permet de choisir
quel compte signe la transaction (utile pour simuler plusieurs professeurs).'''))

# ══════════════════════════════════════════════════════════════════════════════
# CHAPTER 7 — INSTALLATION
# ══════════════════════════════════════════════════════════════════════════════
story.append(PageBreak())
story += section_title('7', 'Installation et Demarrage')

story += subsection_title('7.1', 'Prerequis')
prereqs = [
    'Node.js v18+ et npm',
    'PowerShell (Windows) ou bash (Linux/macOS)',
    'Connexion internet pour la premiere installation (npm packages)',
    'Variable d\'environnement <font name="Courier">ANTHROPIC_API_KEY</font> (cle API Anthropic)',
]
for p_item in prereqs:
    story.append(Paragraph(f'<bullet>\u2022</bullet> {p_item}', bullet_style))
story.append(sp(16))

story += subsection_title('7.2', 'Installation Initiale')
story.append(p('''Executer ces commandes <b>une seule fois</b> depuis la racine du projet pour installer
toutes les dependances et compiler le projet :'''))
story.append(sp(8))
story.append(CodeBlock(
    '# 1. Ajouter System32 au PATH (Windows uniquement)\n'
    '$env:PATH += ";C:\\Windows\\System32"\n'
    '\n'
    '# 2. Se placer dans le dossier du projet\n'
    'cd C:\\Users\\PP\\Desktop\\UEMF\\academic-assistant-final\\final-project\n'
    '\n'
    '# 3. Installer les dependances racine (Hardhat, ethers, scripts)\n'
    'npm install\n'
    '\n'
    '# 4. Installer et compiler le backend TypeScript\n'
    'cd backend\n'
    'npm install\n'
    'npm run build      # Compile TypeScript -> JavaScript (dist/)\n'
    'cd ..\n'
    '\n'
    '# 5. Compiler les smart contracts Solidity\n'
    'npx hardhat compile\n'
    '\n'
    '# 6. Lancer les tests unitaires (optionnel mais recommande)\n'
    'npx hardhat test'
))
story.append(sp(16))

story += subsection_title('7.3', 'Lancement (3 Terminaux Separes)')
story.append(p('''L\'application necessite <b>trois processus en parallele</b>. Ouvrir trois terminaux
PowerShell distincts :'''))
story.append(sp(10))

story.append(p('<b>Terminal 1 — Noeud Blockchain Hardhat</b>', h3))
story.append(CodeBlock(
    '$env:PATH += ";C:\\Windows\\System32"\n'
    'cd C:\\Users\\PP\\Desktop\\UEMF\\academic-assistant-final\\final-project\n'
    'npx hardhat node'
))
story.append(p('''Ce terminal demarre la <b>blockchain Ethereum locale</b>. Il affiche les 20 comptes
de test avec leurs adresses et cles privees. Le noeud RPC ecoute sur
<font name="Courier">http://127.0.0.1:8545</font>. Ce processus doit rester ouvert en permanence.'''))
story.append(sp(12))

story.append(p('<b>Terminal 2 — Serveur Backend API</b>', h3))
story.append(CodeBlock(
    '$env:PATH += ";C:\\Windows\\System32"\n'
    'cd C:\\Users\\PP\\Desktop\\UEMF\\academic-assistant-final\\final-project\\backend\n'
    'npm start'
))
story.append(p('''Ce terminal demarre le <b>serveur Express</b>. Il se connecte automatiquement au
noeud Hardhat via viem, deploie les smart contracts si necessaire, et expose l\'API REST
sur <font name="Courier">http://localhost:3001</font>.'''))
story.append(sp(12))

story.append(p('<b>Terminal 3 — Serveur Frontend</b>', h3))
story.append(CodeBlock(
    '$env:PATH += ";C:\\Windows\\System32"\n'
    'cd C:\\Users\\PP\\Desktop\\UEMF\\academic-assistant-final\\final-project\\frontend\n'
    'npx serve .'
))
story.append(p('''Ce terminal sert les fichiers HTML/CSS/JS statiques. Les deux interfaces
(etudiant et professeur) sont alors accessibles via le navigateur.'''))
story.append(sp(16))

story += subsection_title('7.4', 'Test de l\'API')
story.append(p('''Pour verifier que tous les services fonctionnent correctement, executer :'''))
story.append(CodeBlock(
    '# Depuis la racine du projet\n'
    'node scripts/api_test.js'
))
story.append(p('''Ce script effectue des appels de test automatises sur tous les endpoints
(annonces, documents, IA) et affiche les resultats dans la console.'''))
story.append(sp(12))

story.append(p('<b>URLs d\'acces :</b>'))
urls_data = [
    [Paragraph('<b>Interface</b>', ParagraphStyle('th8', parent=body, textColor=WHITE, fontSize=9, fontName='Helvetica-Bold')),
     Paragraph('<b>URL</b>', ParagraphStyle('th8', parent=body, textColor=WHITE, fontSize=9, fontName='Helvetica-Bold'))],
    ['Etudiant', 'http://localhost:3000/index.html'],
    ['Professeur', 'http://localhost:3000/professor.html'],
    ['API Backend', 'http://localhost:3001/api/'],
    ['Blockchain RPC', 'http://127.0.0.1:8545'],
]
t = Table(urls_data, colWidths=[5*cm, 12*cm])
t.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), PRIMARY),
    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, LIGHT_ACCENT]),
    ('FONTNAME', (0, 1), (-1, -1), 'Courier'),
    ('FONTSIZE', (0, 1), (-1, -1), 9),
    ('GRID', (0, 0), (-1, -1), 0.3, HexColor('#D1D5DB')),
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ('TOPPADDING', (0, 0), (-1, -1), 6),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ('LEFTPADDING', (0, 0), (-1, -1), 10),
]))
story.append(t)

# ══════════════════════════════════════════════════════════════════════════════
# CHAPTER 8 — WORKFLOWS
# ══════════════════════════════════════════════════════════════════════════════
story.append(PageBreak())
story += section_title('8', 'Workflows Utilisateur')

story += subsection_title('8.1', 'Workflow Professeur')
prof_steps = [
    'Ouvrir <font name="Courier">professor.html</font> dans le navigateur',
    '<b>Publier une annonce</b> : aller sur "Publier", remplir contenu/categorie/groupe/index, cliquer "Publier on-chain" → transaction blockchain envoyee et confirmee',
    '<b>Deposer un document</b> : aller sur "Documents", glisser le fichier, remplir le groupe, cliquer "Enregistrer le hash" → SHA-256 enregistre on-chain',
    '<b>Consulter les annonces</b> : aller sur "Annonces" pour voir l\'historique complet',
]
for i, s in enumerate(prof_steps, 1):
    story.append(Paragraph(f'<b>{i}.</b> {s}', ParagraphStyle('step', parent=body, leftIndent=15, spaceAfter=8)))
story.append(sp(16))

story += subsection_title('8.2', 'Workflow Etudiant')
stud_steps = [
    'Ouvrir <font name="Courier">index.html</font> dans le navigateur',
    '<b>Consulter les annonces</b> : onglet "Annonces", filtrer par groupe (ex : MF1), voir les annonces immuables avec horodatage',
    '<b>Verifier un document</b> : onglet "Verifier doc", glisser un fichier → calcul SHA-256 automatique + verification on-chain instantanee',
    '<b>Interroger l\'IA</b> : onglet "Assistant IA", saisir le groupe, poser une question → reponse contextuelle basee sur les annonces blockchain',
]
for i, s in enumerate(stud_steps, 1):
    story.append(Paragraph(f'<b>{i}.</b> {s}', ParagraphStyle('step2', parent=body, leftIndent=15, spaceAfter=8)))

# ══════════════════════════════════════════════════════════════════════════════
# CHAPTER 9 — CONCLUSION
# ══════════════════════════════════════════════════════════════════════════════
story.append(PageBreak())
story += section_title('9', 'Conclusion')

story.append(p('''<b>Academic Assistant</b> demontre avec succes l\'integration de trois technologies
de pointe dans un contexte academique concret : la <b>blockchain Ethereum</b>, la
<b>verification documentaire cryptographique</b>, et l\'<b>intelligence artificielle generative</b>.'''))
story.append(sp(12))

story.append(p('''Le projet repond a une problematique reelle en apportant des garanties fortes :
les annonces academiques sont <b>immuables et horodatees</b>, les documents pedagogiques sont
<b>verifiables sans tiers de confiance</b>, et l\'assistant IA opere sur des <b>donnees
blockchain certifiees</b>, eliminant toute hallucination ou information non verifiee.'''))
story.append(sp(16))

story.append(FeatureBox('Points forts du projet', [
    'Annonces academiques immuables, horodatees et non falsifiables',
    'Verification documentaire decentralisee (sans autorite centrale)',
    'Assistant IA fonctionnant en RAG pur sur donnees blockchain',
    'Architecture full-stack propre avec separation professeur / etudiant',
    'Stack technique moderne : Solidity + TypeScript + viem + Claude API',
    'Interfaces utilisateur ergonomiques et responsives',
]))

story.append(sp(30))
story.append(hr())
story.append(p('Academic Assistant  \xb7  Rapport Technique Final  \xb7  UEMF 2026', caption_style))

# ─── Build PDF ────────────────────────────────────────────────────────────────
OUTPUT = '/mnt/user-data/outputs/Academic_Assistant_Rapport_Technique.pdf'

doc = SimpleDocTemplate(
    OUTPUT,
    pagesize=A4,
    leftMargin=2*cm,
    rightMargin=2*cm,
    topMargin=2.5*cm,
    bottomMargin=2*cm,
    title='Academic Assistant - Rapport Technique',
    author='UEMF',
)

doc.build(story,
    onFirstPage=cover_page,
    onLaterPages=header_footer
)

print(f'PDF generated: {OUTPUT}')