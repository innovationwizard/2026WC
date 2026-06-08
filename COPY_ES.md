# COPY_ES — Glosario de copy en español (única fuente de verdad)

**Propósito:** todo el texto visible para el usuario en este proyecto sale de aquí. Es un glosario **vivo**: cada vez que se introduce una cadena nueva en la web (pasos de la narrativa, etiquetas de UI, microcopy, mensajes de error), se registra su término aprobado en este archivo. Sirve para (a) mantener consistencia entre páginas y (b) que un revisor nativo latinoamericano valide todo en un solo lugar.

**Última actualización:** 2026-06-08

---

## 0. Reglas de registro (obligatorias)
- **Español latinoamericano, trato formal de "usted".** Segunda persona → conjugación de usted ("Seleccione", "Toque", "Filtre"), nunca *tú*. Plural → **ustedes**, nunca *vosotros*. Ver [[spanish-usted-standard]].
- **Sin jerga ni coloquialismos.** Registro neutro, formal, profesional. (Ej. rechazado: *"lo clavó"* → usar **"Marcador exacto"**.)
- **Cuando un verbo en usted choca con la voz del modelo** (1ª/3ª persona), preferir el impersonal: "cuánto no **se sabe**", no "cuánto no sabe(s)".
- **"Marcador" = histórico:** el resultado real de un partido **ya jugado** (p. ej. 2–1).
- **"Predicción" = forecast:** lo que cada **modelo** anticipa. Nunca etiquetar una predicción como "Marcador", ni el marcador real como "Predicción".
- **El tablero de aciertos del sistema se llama "Tablero de aciertos"** (no "marcador de aciertos") para evitar ambigüedad.
- **Números:** separador de miles con coma (10,000), decimal con punto (0.198) — convención de la región del usuario; revisar si se localiza a otro país.

---

## 1. Modelos (los tres)
| Concepto (EN) | Aprobado (ES) | Notas |
|---|---|---|
| The three models (arc) | **Certeza · Inteligencia · Honestidad** | el arco emocional = los 3 modelos (corren **en paralelo**, no en secuencia) |
| Model 1 (M1) | **Modelo 1 — Azar** | Monte Carlo / línea base estocástica (Elo); el contraste "ciego" |
| Model 2 (M2) | **Modelo 2 — Red Neuronal** | la ANN **pura** (Dixon-Coles, bivariate); **sin odds externas** |
| Model 3 (M3) | **Modelo 3 — Conjunto** | ensemble anclado al mercado (ANN+GBT+mercado) **+ intervalos conformal** |
| Market (4.ª línea) | **Mercado** | probabilidades implícitas de las casas de apuestas; la referencia a vencer — muestra **predicción/pick**, no marcador |
| Neural network | **red neuronal** | |
| Monte Carlo simulation | **simulación Monte Carlo** | |
| Expected goals (λ) | **goles esperados (λ)** | |
| Title | **Copa Mundial de la FIFA 2026** · corto: **Mundial 2026** | |

## 2. Estados del partido
| EN | ES | Notas |
|---|---|---|
| Upcoming / scheduled | **Por jugarse** | |
| Live | **En vivo** | con punto pulsante |
| Finished | **Finalizado** | |
| Prediction pending (teams TBD) | **Predicción pendiente — equipos por definir** | partidos de eliminatoria antes de conocerse los clasificados |

## 3. Calendario, navegación y filtros
| EN | ES | Notas |
|---|---|---|
| Context page title | **Contexto — Calendario y Predicciones** | |
| Views toggle | **Lista · Grupos · Llaves** | Lista = por defecto; Llaves = cuadro de eliminatorias |
| Recent (card) | **Recientes** | último día con ≥1 partido finalizado; etiquetar con fecha |
| Up next (card) | **Próximos** | siguiente día con ≥1 partido por jugarse |
| Full calendar | **Calendario completo** | lista agrupada por día, encabezados fijos |
| Filter: group | **Grupo** (chips: Todos · A · B … L) | |
| Filter: stage | **Fase** | ver §4 |
| Filter: team | **Equipo** | búsqueda para seguir a una selección |
| Jump to today | **Ir a hoy** | |
| Tap a date (microcopy) | **Toque una fecha o desplácese** | usted |
| All | **Todos** | |

## 4. Fases del torneo (eliminatoria 48 equipos)
| EN | ES |
|---|---|
| Group stage | **Fase de grupos** |
| Round of 32 | **Dieciseisavos de final** |
| Round of 16 | **Octavos de final** |
| Quarterfinals | **Cuartos de final** |
| Semifinals | **Semifinales** |
| Final | **Final** |
| (Group advance) | **Avanza** |
| Champion | **Campeón** |

## 5. Predicción, resultado y aciertos
| EN | ES | Notas |
|---|---|---|
| Forecast / prediction | **Predicción** | lo que anticipa cada modelo |
| Predicted scoreline (in-row) | **Predicción** (p. ej. 2–1) | el marcador más probable (modal) por modelo; la etiqueta es "Predicción", **no** "Marcador" |
| Actual (historic) scoreline | **Marcador** (p. ej. 2–1) | el resultado real de un partido ya jugado |
| Outcome (W/D/L) | **Resultado** | el desenlace (victoria/empate/derrota), distinto del marcador |
| Correct pick | **Acierto** (✓) | calificado por resultado 1/X/2 |
| Wrong pick | **Fallo** (✗) | |
| Exact-score hit (badge) | **Marcador exacto** (⭐) | la predicción igualó el marcador histórico; NUNCA "lo clavó" |
| Exact-score tally | **N exactos** | p. ej. "2 exactos" |
| Accuracy scoreboard | **Tablero de aciertos** | NO "marcador de aciertos" (ambiguo) |
| Hit-rate (headline, a color) | **aciertos** — "8/12 aciertos" | color de alto contraste |
| RPS (secondary, tenue) | **RPS** | gloss opcional: "(puntuación de probabilidad ordenada)" |
| Small-sample tag | **(muestra pequeña)** | bajo ~20 partidos |
| Outcome labels | **victoria · empate · derrota** | |

## 6. Términos estadísticos / Modelo 3
| EN | ES |
|---|---|
| Champion probability | **Probabilidad de ser campeón** |
| Stage probability | **Probabilidad por etapa** |
| Conformal interval | **intervalo conformal** |
| Coverage | **cobertura** |
| Calibration | **calibración** |
| Reliability diagram | **diagrama de calibración** |
| Simulation band (NOT a guarantee) | **banda de simulación** | aclarar: "no es garantía de cobertura" |
| Squad market value | **valor de mercado del plantel** |
| National team | **selección** |

## 7. Microcopy / botones
| EN | ES |
|---|---|
| Scroll cue (hero) | **▼ Desplácese** |
| Autoplay | **Reproducción automática** · botón: **▶ Reproducir solo** |
| Methodology | **Metodología** |
| Credits | **Créditos** |
| Replay | **Repetir** |

## 8. Frases clave aprobadas (verbatim)
- Hero: **"¿Quién gana el Mundial 2026? — ¿y cómo lo sabría?"**
- Tesis (final): **"Cuando difiero del mercado, el backtest se ganó el derecho."**
- Honestidad (Modelo 3): **"Lo más sofisticado no es la respuesta. Es saber cuánto no se sabe — y probarlo."**
> Las líneas completas de narración por paso viven en `WEBSITE_STORYTELLING_DESIGN.md` (§4); también deben pasar por revisión nativa.

## 9. Términos rechazados (no usar)
| ✗ Rechazado | ✓ Usar | Motivo |
|---|---|---|
| "lo clavó" | **Marcador exacto** | jerga; mal español formal (corrección de Jorge, 2026-06-08) |
| "Marcador de aciertos" | **Tablero de aciertos** | "Marcador" se reserva para el marcador histórico de un partido |
| "Pronóstico" (para el forecast) | **Predicción** | término canónico (consistente con v1 y con la distinción Marcador/Predicción) |
| "Ronda" / "Round" (para los 3 modelos) | **Modelo** (M1/M2/M3) | "round" implica secuencia temporal; los 3 modelos corren en paralelo (corrección de Jorge, 2026-06-08) |
| Imperativos en *tú* ("Multiplícalo", "Córrelo", "Tíralo") | usted ("Multiplíquelo", "Córralo", "Tírelo") | registro formal |

## 10. Pendiente de revisión nativa
- [ ] Todo el texto de UI y narración antes del lanzamiento — un hablante nativo LatAm valida registro y naturalidad (el generador de este copy no es nativo).
- [ ] Confirmar "Llaves" vs "Cuadro" para el bracket según preferencia regional del público.
- [ ] Confirmar convención numérica (coma de miles / punto decimal) para el país objetivo.
- [ ] **Nombres de selección (display GUI, en `web/src/lib/teams.js`):** confirmar formas cortas/traducciones — Chequia, Corea, EE. UU., P. Bajos, A. Saudita, C. de Marfil, N. Zelanda, RD Congo, Catar, Curazao, Sudáfrica. Banderas de Inglaterra/Escocia usan emoji de subdivisión (🏴 + tags) — puede mostrarse como bandera negra en algunos sistemas.

---

## 11. Microcopy implementada — Context page (para revisión nativa)
Cadenas ya en código (`web/src/`), todas en usted/neutro:
| Ubicación | Cadena |
|---|---|
| Título | **Contexto — Calendario y Predicciones** |
| Subtítulo | **Copa Mundial de la FIFA 2026 · {N} partidos de fase de grupos** |
| Tablero | **Tablero de aciertos** · **(muestra pequeña)** |
| Tablero (vacío) | **Se activa cuando se jueguen los primeros partidos. Por ahora muestra los pronósticos de cada modelo en el calendario.** |
| Tablero (por línea) | **{n}/{N} aciertos** · **RPS {x}** · **{n} exactos** |
| Tarjetas | **Recientes** · **Próximos** |
| Recientes (vacío) | **Aún no hay partidos jugados.** |
| Próximos (vacío) | **Sin próximos partidos.** |
| Calendario | **Calendario completo** · **{n} de {N}** |
| Filtros | chips **Todos / A … L** · buscador placeholder **Buscar selección…** |
| Calendario (vacío) | **Sin resultados para este filtro.** |
| Estado partido | **Por jugarse** · **En vivo** · **Finalizado** |
| Fila (etiquetas) | **Grupo {X}** · **L {p}% · E {p}% · V {p}%** (Local/Empate/Visitante) · **xG {a}–{b}** · **favorito: {equipo}** · **intervalo [{lo}–{hi}%]** · **— pendiente** |
| Veredicto | **✓** acierto · **✗** fallo · **⭐** marcador exacto |
| Grupos (encabezados) | **Selección · Elo · Valor · Avanza · Campeón** |
| Grupos (tooltip «Valor») | **Valor de mercado del plantel (millones de €, Transfermarkt)** · sin dato → **—** |
| Llaves | nota **El cuadro exacto se define al terminar la fase de grupos…** · encabezados **Octavos · Cuartos · Semis · Final · Campeón** |
