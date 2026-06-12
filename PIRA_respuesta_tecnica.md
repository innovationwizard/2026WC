# PIRA — Respuesta técnica sobre los tres (cuatro) modelos

> Borrador de respuesta para PIRA (PhD en Estadística). Registro técnico, vocabulario completo.
> Estructura: (1) la especificación exacta de nuestros modelos — las "condiciones" que pregunta;
> (2) comentario punto por punto a sus tres enfoques; (3) el tema de fondo: *"no es mucha la
> diferencia entre uno y otro"*; (4) una propuesta de terreno común reproducible.

---

Gracias por compartir su procedimiento con ese nivel de detalle — me deja comparar manzanas con
manzanas. Antes de entrar a sus tres enfoques, le aclaro las "condiciones" de cada uno de los
míos, porque sin la especificación la comparación es ciega.

---

## 1. La especificación de los cuatro modelos

No son tres variantes del mismo objeto: son tres **pronosticadores de punto distintos** más una
**línea de mercado** como referencia externa. Todos producen, por partido, una **distribución de
goles** (no un número), y de ahí $P(\text{Local}/\text{Empate}/\text{Visitante})$ y el marcador
modal. El torneo se resuelve con **Monte Carlo** (10 000 simulaciones del cuadro completo).

- **M1 — "Azar" (línea base Elo).** Es deliberadamente un *foil*: goles como Poisson independientes
  con $\lambda$ derivado **solo** del Elo vía la curva logística de puntuación esperada,
  $p_A = \big(1+10^{-(E_A-E_B)/400}\big)^{-1}$, $\lambda_A = \bar g\,(0{,}5 + p_A)$, con
  $\bar g = 1{,}35$. Sin aprendizaje. Es el *null model* contra el cual mido si la red aporta algo.

- **M2 — "Red Neuronal" (regresión de Poisson neuronal, *ensembled*).** Una red feedforward
  produce $\lambda = \mathrm{softplus}(f_\theta(x))$ a partir de **47 covariables** (Elo, forma
  reciente con rezago correcto, valor de plantel, PIB/población, confederación, localía/sede,
  historia mundialista, etc.), entrenada **minimizando la log-verosimilitud de Poisson**
  (la *deviance*), $\mathcal{L} = \lambda - y\log\lambda$. Es, formalmente, una **regresión de
  Poisson no paramétrica** con enlace logarítmico. Uso un **ensemble de $M=50$ redes** (distintas
  semillas) promediado sobre $\lambda$, porque una sola red **no era reproducible**: el campeón
  saltaba (Brasil 23 % ↔ 11,6 %) entre semillas — varianza de optimización, no señal. El promedio
  la colapsa.

- **M3 — "Conjunto".** Mezcla convexa de **dos familias distintas**:
  $\lambda_{M3} = w\,\lambda_{\text{red}} + (1-w)\,\lambda_{\text{GBT}}$, con $w=0{,}5$ **elegido por
  backtest**, no a dedo. El segundo miembro es un **gradient boosting de Poisson** (HistGradientBoosting,
  `loss="poisson"`) — particionamiento axis-aligned en vez de interpolación suave. Encima va una capa
  de **predicción conformal** (LAC, *Least Ambiguous set-valued Classifier*) que entrega **conjuntos
  de resultados plausibles** con **cobertura marginal $\ge 1-\alpha$ de muestra finita y libre de
  distribución**, bajo el único supuesto de **intercambiabilidad**.

- **Mercado.** Probabilidades implícitas **sin vig**: $1/\text{cuota}$ normalizado para remover el
  *overround*. Es el consenso, no un modelo mío; lo pongo como vara externa.

Dos correcciones que valen la pena mencionar porque son justo el tipo de cosa que un estadístico
huele: (a) **fuga de información / *look-ahead bias*** — las medias móviles de forma incluían el
partido en curso (¡el propio *target*!) por falta de un `shift(1)`; al corregirlo la *deviance*
**dentro de muestra empeoró** (0,66 → 0,78), que es exactamente la firma de quitar el atisbo al
futuro, y **fuera de muestra mejoró**. (b) un sesgo en el sorteo del cuadro que distorsionaba las
rondas por letra de grupo, no por mérito.

---

## 2. Sobre sus tres enfoques

### 2.1 Mínimos cuadrados para estimar goles

Es un primer paso razonable e interpretable, pero OLS sobre un **conteo** pelea con sus propios
supuestos:

- **Soporte y forma.** Los goles son enteros no negativos; OLS puede predecir valores negativos y
  asume errores gaussianos homocedásticos. En conteos $\mathrm{Var}(Y\mid X)$ **crece con la media**
  (equidispersión de Poisson, o sobredispersión), así que OLS es **heterocedástico**, deja de ser
  BLUE y sus errores estándar quedan mal calibrados.
- **La verosimilitud correcta.** El estimador natural es un **GLM de Poisson con enlace log**
  (o **binomial negativa** si hay sobredispersión, que en goles de selecciones la suele haber). Mi
  M2/M3 son precisamente eso, pero con el predictor lineal reemplazado por una red / un ensemble de
  árboles: maximizo la verosimilitud de Poisson, no la suma de cuadrados.
- **De goles a resultado.** El punto fino: para pasar de "goles esperados de cada uno" a
  $P(\text{L}/\text{E}/\text{V})$ se necesita la **distribución conjunta** de $(G_A, G_B)$. Poisson
  la regala (convolución / matriz de marcadores), y con ella el pronóstico es **probabilístico** y
  por lo tanto **puntuable con una regla propia y calibrable**. Un punto de OLS, sin imponer una
  distribución a los residuos, no le da esa distribución sobre resultados.
- **Refinamiento estándar.** Si quisiera quedarse en la familia Poisson, **Dixon-Coles (1997)**
  corrige la dependencia en marcadores bajos (0-0, 1-0, 0-1, 1-1) y agrega **ponderación con
  decaimiento temporal**. Es el camino "clásico" y muy defendible.

### 2.2 El valor de Shapley para "ponerlos a jugar"

Aquí me gustaría entender mejor la construcción, porque el **valor de Shapley** (Shapley, 1953) es la
única **atribución** que satisface eficiencia, simetría, jugador nulo y aditividad: reparte el valor
de una **función característica** $v(S)$ entre jugadores. En ML eso es **SHAP** (Lundberg & Lee,
2017): atribución de la predicción **entre las features**. Es una herramienta de **interpretación**,
no un **mecanismo generativo/predictivo**.

- La pregunta clave es **cuál fue su $v(S)$** y **quiénes eran los "jugadores"** (¿las variables?,
  ¿los equipos?, ¿los modelos?). Sin una función característica bien definida, lo que devuelve la IA
  puede sonar plausible pero estar **mal definido** — un número sin estimando.
- Costo: Shapley exacto es **exponencial** ($2^n$ coaliciones); en la práctica se aproxima
  (KernelSHAP, o TreeSHAP exacto para árboles).
- Dónde **sí** encaja con rigor en este problema: explicar el $\lambda$ de un partido **atribuyéndolo
  a las features** (por qué la red ve a España fuerte pese a marcar poco). Eso es justo una capa de
  interpretabilidad que tengo pendiente de exponer — pero insisto: explica un pronóstico, no lo
  produce.

### 2.3 La predicción "pelada" de la IA

Pedirle al LLM su mejor pronóstico es usarlo como **pronosticador zero-shot**, y trae problemas
conocidos:

- **Sin modelo probabilístico explícito** ni garantía de **calibración**: las probabilidades que
  emite no tienen por qué cumplir $P \approx$ frecuencia observada.
- **Contaminación / fuga de datos.** El LLM ya vio, hasta su corte, el **consenso pre-torneo**, las
  cuotas y las predicciones de expertos. Para un torneo **futuro** no vio resultados, pero **sí vio
  el consenso de mercado** → lo **regurgita**. Por eso "coincide con todo": no es un modelo
  independiente, es un *prior* de consenso disfrazado de predicción.
- **No reproducible** (temperatura, sensibilidad al *prompt*, versión del modelo), **no auditable** y
  **no se le puede hacer backtest** como objeto estable.
- Como **prior de consenso**, sin embargo, es fortísimo — y eso, creo, explica en buena parte por qué
  **sus tres métodos coinciden entre sí**: si dos de los tres pasan por la misma IA / el mismo
  consenso, están bebiendo de la misma fuente.

---

## 3. El tema de fondo: *"no es mucha la diferencia entre uno y otro"*

Coincido con la observación, y es el punto más interesante. Pero "poca diferencia" merece un
tratamiento más fino que el de la intuición.

**(a) La convergencia es esperada — y es buena noticia.** Métodos razonables entrenados sobre la
**misma señal informativa** convergen al mismo $\mathbb{E}[Y\mid X]$ a medida que se acercan al
predictor de **Bayes**. La componente **predecible** del fútbol es chica: un partido es, en buena
medida, una realización de una distribución de **alta varianza aleatoria (irreducible)**. Una vez que
capturás fuerza de equipo + localía/neutralidad + un puñado de covariables, ya estás cerca del
**piso de error irreducible**, y la sofisticación adicional rinde **retornos decrecientes**. Que los
métodos disten poco es **evidencia de que todos rondamos ese piso**, no de que sean intercambiables.

**(b) "Poca diferencia" hay que medirla con una regla de puntuación propia, no a ojo.** Dos
pronosticadores pueden parecer iguales en el punto y diferir en **habilidad probabilística**. Lo
cuantifico con el **RPS (Ranked Probability Score)** — regla **propia** y sensible a toda la
distribución ordinal — sobre un **backtest temporal** (entreno ≤2024, pruebo 2025+, **1 267 partidos
no vistos**):

> **M3 0,165 < M2 0,166 < Elo 0,175.**  (~6 % relativo de mejora sobre el Elo puro.)

Y las diferencias pequeñas **por partido se acumulan**: ese mismo backtest, cuando corregí la fuga de
información, movió a **España del 3,6 % al 19 %** de probabilidad de campeón. Métrica por partido
minúscula, consecuencia a nivel de torneo enorme — porque el Monte Carlo del cuadro **propaga** ese
sesgo a lo largo de siete rondas. "Poca diferencia media por partido" $\neq$ "poca diferencia en la
salida que importa".

**(c) La diferencia que de verdad importa no es el punto: es la calibración y la cuantificación de
incertidumbre.** Tres pronosticadores de punto coincidiendo no dicen **nada** sobre si sus
**probabilidades** están calibradas. Ahí está mi aporte: un **diagrama de fiabilidad** (que cae sobre
la diagonal: cuando digo 70 %, ocurre ~70 %) y **conjuntos conformes** con **garantía de cobertura de
muestra finita** sin supuestos distribucionales. Un número de OLS o un número "pelado" del LLM **no
tiene cobertura** — no es comparable en esa dimensión.

**(d) Coincidir $\neq$ acertar; cuidado con el sesgo compartido.** Si sus tres métodos enrutan por
una IA y un *prior* de mercado, **comparten un sesgo de consenso**, y entonces su acuerdo es en parte
**artefacto de un prior común**, no corroboración independiente. El beneficio real de un ensemble
exige **errores diversos y débilmente correlacionados** — la **descomposición de ambigüedad de
Krogh–Vedelsby**: $\;E_{\text{ens}} = \overline{E}_{\text{ind}} - \overline{A}\;$ (error del ensemble
= error promedio individual − ambigüedad/diversidad). Por eso mezclé **dos familias deliberadamente
distintas** (interpolación suave de la red + partición por árboles), cuyos errores están
**parcialmente decorrelacionados**; el backtest confirmó que la mezcla 50/50 **le gana a ambos
constituyentes** ($0{,}1648 < 0{,}1655$ red, $< 0{,}1653$ GBT). Esa es la justificación formal del
"Conjunto", no la estética.

**(e) Cómo testear "la diferencia" como se debe — y el resultado.** La forma rigurosa de evaluar
*"no es mucha la diferencia"* es una **prueba de Diebold–Mariano (1995)** sobre la serie de
**diferenciales de pérdida** (RPS) partido a partido, con la corrección de muestra finita de
**Harvey–Leybourne–Newbold (1997)** y p-valores $t_{n-1}$. La corrí sobre los **1 267 partidos fuera
de muestra** (orden cronológico, horizonte $h=1$, diferenciales no solapados ⇒ la varianza de largo
plazo es la varianza muestral):

| par | media $\Delta$RPS | DM | $p$ (2 colas) | veredicto |
|---|---:|---:|---:|---|
| **M2 vs M1** (Elo) | $-0{,}00909$ | $-5{,}21$ | $2{,}3\times10^{-7}$ | M2 mejor — **significativo** |
| **M3 vs M1** (Elo) | $-0{,}00970$ | $-5{,}90$ | $4{,}7\times10^{-9}$ | M3 mejor — **significativo** |
| **M3 vs M2** | $-0{,}00061$ | $-1{,}06$ | $0{,}29$ | M3 mejor — **no significativo** |

La lectura es de **dos partes**, y es justo lo interesante de su observación:

- **Contra el Elo, "poca diferencia" es falso.** Una brecha media de apenas ~0,009 de RPS resulta
  **abrumadoramente significativa** ($p \sim 10^{-7}$–$10^{-9}$): media chica **+ baja varianza del
  diferencial** $\Rightarrow$ DM de $-5$ a $-6$. La sofisticación **sí** compra habilidad medible; no
  es ruido.
- **Entre los dos modelos buenos (M3 vs M2), "poca diferencia" es verdadero.** $p=0{,}29$: la mezcla
  mejora la **dirección** pero **no es estadísticamente distinguible** del net en este conjunto. Ahí
  su intuición da en el clavo — y por eso el lugar para competir entre buenos modelos no es el punto,
  sino la **calibración y la incertidumbre** (punto (c)).

Una sutileza que conviene decir de frente: donde un modelo **anida** al otro (la red usa el Elo como
una de sus 47 features; M2 es el caso $w=1$ de la familia de M3), el DM es **conservador** y
**Clark–West (2007)** sería más potente — de modo que un **rechazo es una cota inferior robusta**. Que
M2-vs-Elo rechace con $p\sim10^{-7}$ **a pesar** del anidamiento es, por eso, un resultado fuerte.
"Numéricamente chico" no es "estadísticamente indistinguible": el DM separa los dos casos limpiamente.

---

## 4. Una propuesta de terreno común

Lo más entretenido sería zanjarlo de forma reproducible: correr **sus tres** y **mis cuatro** sobre
**el mismo split fuera de muestra**, con **la misma regla propia** (RPS / Brier / log-loss),
**diagramas de fiabilidad** lado a lado, y una **prueba de Diebold–Mariano** por pares. Con mucho
gusto le paso el *harness* de backtest y la partición temporal para que no haya discusión sobre el
*setup*. Si sus tres convergen y los míos también, **y los siete caen cerca en RPS calibrado**, eso
ya sería un resultado bonito por sí mismo: estaríamos todos tocando el piso de Bayes del problema.

---

## 5. En una frase

El objetivo nunca fue **"ganarle"** al consenso — el mercado es difícil de batir (eficiencia
semifuerte). Fue: **(1)** llegar al consenso de forma **independiente y desde datos crudos** (lo que
valida el *pipeline*), **(2)** ser **honesto con la incertidumbre** (conformal + calibración), y
**(3)** ser **auditable y reproducible** — cada cifra rastrea a datos + un procedimiento fijo, sin
ajuste a mano. La afirmación no es "mi número es más correcto"; es "**mi número está ganado y
medido**". Que los métodos converjan no me preocupa: me dice que el problema tiene poco jugo
predecible que exprimir, y que conviene competir en **calibración y honestidad**, no en el segundo
decimal del punto.

— Un gusto la conversación; encantado de seguirla con los números sobre la mesa.
