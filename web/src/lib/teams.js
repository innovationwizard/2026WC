// GUI-only team display (NOT data): flag + short name for single-line rows,
// full name for headers / hover tooltip. Data keeps canonical (CSV) names;
// this module is the presentation source of truth.
// ⚠ Spanish short/full names + a couple of flags PENDING native review (COPY_ES §10):
//    Chequia · Corea · EE. UU. · P. Bajos · A. Saudita · C. de Marfil · N. Zelanda · RD Congo
//    England/Scotland use subdivision flag emoji (may fall back to a black flag on some OSes).

export const TEAMS = {
  // Group A
  'Mexico':                 { full: 'México',                 short: 'México',        flag: '🇲🇽' },
  'South Africa':           { full: 'Sudáfrica',              short: 'Sudáfrica',     flag: '🇿🇦' },
  'South Korea':            { full: 'Corea del Sur',          short: 'Corea',         flag: '🇰🇷' },
  'Czech Republic':         { full: 'República Checa',        short: 'Chequia',       flag: '🇨🇿' },
  // Group B
  'Canada':                 { full: 'Canadá',                 short: 'Canadá',        flag: '🇨🇦' },
  'Bosnia and Herzegovina': { full: 'Bosnia y Herzegovina',   short: 'Bosnia',        flag: '🇧🇦' },
  'Qatar':                  { full: 'Catar',                  short: 'Catar',         flag: '🇶🇦' },
  'Switzerland':            { full: 'Suiza',                  short: 'Suiza',         flag: '🇨🇭' },
  // Group C
  'Brazil':                 { full: 'Brasil',                 short: 'Brasil',        flag: '🇧🇷' },
  'Morocco':                { full: 'Marruecos',              short: 'Marruecos',     flag: '🇲🇦' },
  'Haiti':                  { full: 'Haití',                  short: 'Haití',         flag: '🇭🇹' },
  'Scotland':               { full: 'Escocia',                short: 'Escocia',       flag: '🏴\u{E0067}\u{E0062}\u{E0073}\u{E0063}\u{E0074}\u{E007F}' },
  // Group D
  'United States':          { full: 'Estados Unidos',         short: 'EE. UU.',       flag: '🇺🇸' },
  'Paraguay':               { full: 'Paraguay',               short: 'Paraguay',      flag: '🇵🇾' },
  'Australia':              { full: 'Australia',              short: 'Australia',     flag: '🇦🇺' },
  'Turkey':                 { full: 'Turquía',                short: 'Turquía',       flag: '🇹🇷' },
  // Group E
  'Germany':                { full: 'Alemania',               short: 'Alemania',      flag: '🇩🇪' },
  'Curaçao':                { full: 'Curazao',                short: 'Curazao',       flag: '🇨🇼' },
  'Ivory Coast':            { full: 'Costa de Marfil',        short: 'C. de Marfil',  flag: '🇨🇮' },
  'Ecuador':                { full: 'Ecuador',                short: 'Ecuador',       flag: '🇪🇨' },
  // Group F
  'Netherlands':            { full: 'Países Bajos',           short: 'P. Bajos',      flag: '🇳🇱' },
  'Japan':                  { full: 'Japón',                  short: 'Japón',         flag: '🇯🇵' },
  'Sweden':                 { full: 'Suecia',                 short: 'Suecia',        flag: '🇸🇪' },
  'Tunisia':                { full: 'Túnez',                  short: 'Túnez',         flag: '🇹🇳' },
  // Group G
  'Belgium':                { full: 'Bélgica',                short: 'Bélgica',       flag: '🇧🇪' },
  'Egypt':                  { full: 'Egipto',                 short: 'Egipto',        flag: '🇪🇬' },
  'Iran':                   { full: 'Irán',                   short: 'Irán',          flag: '🇮🇷' },
  'New Zealand':            { full: 'Nueva Zelanda',          short: 'N. Zelanda',    flag: '🇳🇿' },
  // Group H
  'Spain':                  { full: 'España',                 short: 'España',        flag: '🇪🇸' },
  'Cape Verde':             { full: 'Cabo Verde',             short: 'Cabo Verde',    flag: '🇨🇻' },
  'Saudi Arabia':           { full: 'Arabia Saudita',         short: 'A. Saudita',    flag: '🇸🇦' },
  'Uruguay':                { full: 'Uruguay',                short: 'Uruguay',       flag: '🇺🇾' },
  // Group I
  'France':                 { full: 'Francia',                short: 'Francia',       flag: '🇫🇷' },
  'Senegal':                { full: 'Senegal',                short: 'Senegal',       flag: '🇸🇳' },
  'Iraq':                   { full: 'Irak',                   short: 'Irak',          flag: '🇮🇶' },
  'Norway':                 { full: 'Noruega',                short: 'Noruega',       flag: '🇳🇴' },
  // Group J
  'Argentina':              { full: 'Argentina',              short: 'Argentina',     flag: '🇦🇷' },
  'Algeria':                { full: 'Argelia',                short: 'Argelia',       flag: '🇩🇿' },
  'Austria':                { full: 'Austria',                short: 'Austria',       flag: '🇦🇹' },
  'Jordan':                 { full: 'Jordania',               short: 'Jordania',      flag: '🇯🇴' },
  // Group K
  'Portugal':               { full: 'Portugal',               short: 'Portugal',      flag: '🇵🇹' },
  'DR Congo':               { full: 'RD del Congo',           short: 'RD Congo',      flag: '🇨🇩' },
  'Uzbekistan':             { full: 'Uzbekistán',             short: 'Uzbekistán',    flag: '🇺🇿' },
  'Colombia':               { full: 'Colombia',               short: 'Colombia',      flag: '🇨🇴' },
  // Group L
  'England':                { full: 'Inglaterra',             short: 'Inglaterra',    flag: '🏴\u{E0067}\u{E0062}\u{E0065}\u{E006E}\u{E0067}\u{E007F}' },
  'Croatia':                { full: 'Croacia',                short: 'Croacia',       flag: '🇭🇷' },
  'Ghana':                  { full: 'Ghana',                  short: 'Ghana',         flag: '🇬🇭' },
  'Panama':                 { full: 'Panamá',                 short: 'Panamá',        flag: '🇵🇦' },
};

export const teamFull  = (c) => TEAMS[c]?.full  ?? c;
export const teamShort = (c) => TEAMS[c]?.short ?? TEAMS[c]?.full ?? c;
export const teamFlag  = (c) => TEAMS[c]?.flag  ?? '';

// FIFA 3-letter codes (for compact tables, e.g. the printable bracket group tables).
export const CODES = {
  'Mexico': 'MEX', 'South Africa': 'RSA', 'South Korea': 'KOR', 'Czech Republic': 'CZE',
  'Canada': 'CAN', 'Bosnia and Herzegovina': 'BIH', 'Qatar': 'QAT', 'Switzerland': 'SUI',
  'Brazil': 'BRA', 'Morocco': 'MAR', 'Haiti': 'HAI', 'Scotland': 'SCO',
  'United States': 'USA', 'Paraguay': 'PAR', 'Australia': 'AUS', 'Turkey': 'TUR',
  'Germany': 'GER', 'Curaçao': 'CUW', 'Ivory Coast': 'CIV', 'Ecuador': 'ECU',
  'Netherlands': 'NED', 'Japan': 'JPN', 'Sweden': 'SWE', 'Tunisia': 'TUN',
  'Belgium': 'BEL', 'Iran': 'IRN', 'Egypt': 'EGY', 'New Zealand': 'NZL',
  'Cape Verde': 'CPV', 'Saudi Arabia': 'KSA', 'Uruguay': 'URU', 'Spain': 'ESP',
  'France': 'FRA', 'Iraq': 'IRQ', 'Norway': 'NOR', 'Senegal': 'SEN',
  'Argentina': 'ARG', 'Austria': 'AUT', 'Algeria': 'ALG', 'Jordan': 'JOR',
  'Portugal': 'POR', 'Uzbekistan': 'UZB', 'Colombia': 'COL', 'DR Congo': 'COD',
  'England': 'ENG', 'Ghana': 'GHA', 'Panama': 'PAN', 'Croatia': 'CRO',
};
export const teamCode = (c) => CODES[c] ?? (TEAMS[c]?.short ?? c).slice(0, 3).toUpperCase();
