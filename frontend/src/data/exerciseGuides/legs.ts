import type { ExerciseGuide } from './types';

// Free Exercise DB (public domain): level and muscles as published;
// steps translated to Spanish and condensed from its instructions.
export const LEGS_GUIDES: Record<string, ExerciseGuide> = {
  'Thigh_Abductor': {
    level: 'beginner',
    primaryMuscles: ['abductors'],
    secondaryMuscles: ['glutes'],
    steps: [
      'Siéntate en la máquina de abductores, elige un peso cómodo y coloca las piernas en las almohadillas.',
      'Agarra los asideros laterales y mantén todo el torso quieto, de la cintura hacia arriba: es la posición inicial.',
      'Empuja despacio con las piernas para separarlas mientras espiras.',
      'Mantén la contracción un segundo y vuelve a juntar las piernas despacio mientras inspiras.',
      'No muevas el torso en ningún momento para evitar lesiones.',
    ],
  },
  'Thigh_Adductor': {
    level: 'beginner',
    primaryMuscles: ['adductors'],
    secondaryMuscles: ['glutes', 'hamstrings'],
    steps: [
      'Siéntate en la máquina de aductores, elige un peso cómodo y apoya las piernas en las almohadillas.',
      'Agarra los asideros laterales y mantén todo el torso quieto, de la cintura hacia arriba: es la posición inicial.',
      'Empuja despacio con las piernas para juntarlas mientras espiras.',
      'Mantén la contracción un segundo y vuelve a separar las piernas despacio mientras inspiras.',
      'No muevas el torso ni hagas tirones bruscos para evitar lesiones.',
    ],
  },
  'Split_Squat_with_Dumbbells': {
    level: 'beginner',
    primaryMuscles: ['quadriceps'],
    secondaryMuscles: ['glutes', 'hamstrings'],
    steps: [
      'Colócate con una pierna adelantada y el pie de atrás elevado sobre un banco.',
      'Sujeta una mancuerna en cada mano con los brazos colgando a los lados: es la posición inicial.',
      'Baja flexionando la rodilla y la cadera de la pierna delantera, con el torso erguido y la rodilla alineada con el pie.',
      'Desde abajo, empuja con el talón para extender rodilla y cadera y volver a la posición inicial.',
    ],
  },
  'Standing_Calf_Raises': {
    level: 'beginner',
    primaryMuscles: ['calves'],
    secondaryMuscles: [],
    steps: [
      'Elige el peso y ajusta la máquina a tu altura. Coloca los hombros bajo las almohadillas y la punta de los pies sobre la plataforma, con los talones en el aire.',
      'Extiende caderas y rodillas hasta quedar erguido, con las rodillas ligeramente flexionadas, nunca bloqueadas: es la posición inicial.',
      'Eleva los talones todo lo que puedas mientras espiras, contrayendo los gemelos y sin mover las rodillas. Aguanta un segundo arriba.',
      'Baja los talones despacio mientras inspiras hasta notar el estiramiento de los gemelos.',
    ],
  },
  'Glute_Kickback': {
    level: 'beginner',
    primaryMuscles: ['glutes'],
    secondaryMuscles: ['hamstrings'],
    steps: [
      'Ponte a cuatro patas en el suelo o en una esterilla, con las manos a la anchura de los hombros, la mirada al frente y las rodillas a 90°: es la posición inicial.',
      'Mientras espiras, eleva una pierna manteniendo los 90° hasta que el muslo quede en línea con la espalda, paralelo al suelo, y la pantorrilla vertical.',
      'Contrae el glúteo durante todo el recorrido y aguanta la contracción un segundo arriba.',
      'Vuelve a la posición inicial mientras inspiras y repite con la otra pierna, alternando.',
    ],
  },
  'Hack_Squat': {
    level: 'beginner',
    primaryMuscles: ['quadriceps'],
    secondaryMuscles: ['calves', 'glutes', 'hamstrings'],
    steps: [
      'Apoya la espalda en el respaldo y los hombros bajo las almohadillas. Coloca los pies en la plataforma a la anchura de los hombros, con las puntas algo hacia fuera.',
      'Agarra los asideros laterales, quita los seguros y extiende las piernas sin bloquear las rodillas: es la posición inicial.',
      'Inspira y baja despacio flexionando las rodillas, con la cabeza alta y la espalda siempre pegada al respaldo, hasta pasar un poco de los 90°.',
      'Las rodillas no deben sobrepasar la punta de los pies: si lo hacen, estás sobrecargando la rodilla.',
      'Empuja sobre todo con los talones y extiende las piernas mientras espiras hasta volver a la posición inicial.',
    ],
  },
  'Barbell_Hip_Thrust': {
    level: 'intermediate',
    primaryMuscles: ['glutes'],
    secondaryMuscles: ['calves', 'hamstrings'],
    steps: [
      'Siéntate en el suelo con el banco o el respaldo detrás de ti y la barra o la almohadilla de la máquina sobre las piernas.',
      'Coloca la carga justo encima de las caderas y apoya la parte alta de la espalda, con las escápulas cerca del borde superior del banco o del respaldo.',
      'Si usas barra, una almohadilla o una barra gruesa reduce mucho la molestia.',
      'Empuja con los pies y extiende las caderas hacia arriba todo lo que puedas; el peso recae en las escápulas y los pies.',
      'Invierte el movimiento para volver a la posición inicial.',
    ],
  },
  'Lying_Leg_Curls': {
    level: 'beginner',
    primaryMuscles: ['hamstrings'],
    secondaryMuscles: [],
    steps: [
      'Elige el peso, ajusta la palanca a tu altura y túmbate boca abajo con el rodillo apoyado detrás de las piernas, unos centímetros por debajo de los gemelos.',
      'Con el torso pegado al banco, las piernas estiradas y las puntas de los pies rectas, agarra los asideros laterales: es la posición inicial.',
      'Mientras espiras, flexiona las piernas todo lo que puedas sin despegar los muslos de la almohadilla y aguanta un segundo arriba.',
      'Mientras inspiras, vuelve a bajar las piernas despacio hasta la posición inicial.',
      'Si puedes, usa una máquina inclinada en vez de plana: recluta mejor los isquios.',
    ],
  },
  'Leg_Extensions': {
    level: 'beginner',
    primaryMuscles: ['quadriceps'],
    secondaryMuscles: [],
    steps: [
      'Elige el peso y siéntate con las piernas bajo el rodillo, los pies al frente y las manos en los asideros laterales: es la posición inicial.',
      'Ajusta el rodillo para que apoye justo encima de los pies y comprueba que las piernas forman 90°; si el ángulo es menor, la rodilla sobrepasa la punta del pie.',
      'Extiende las piernas al máximo con los cuádriceps mientras espiras, sin mover el resto del cuerpo del asiento. Aguanta un segundo arriba.',
      'Baja el peso despacio mientras inspiras, sin pasar de los 90°.',
    ],
  },
  'Leg_Press': {
    level: 'beginner',
    primaryMuscles: ['quadriceps'],
    secondaryMuscles: ['calves', 'glutes', 'hamstrings'],
    steps: [
      'Siéntate y apoya los pies en la plataforma, separados a la anchura de los hombros.',
      'Quita los seguros y empuja hasta extender las piernas, sin bloquear las rodillas. Torso y piernas forman 90°: es la posición inicial.',
      'Inspira y baja la plataforma despacio hasta que las rodillas formen 90°.',
      'Empuja sobre todo con los talones y vuelve arriba mientras espiras.',
      'Al terminar, vuelve a poner los seguros: la plataforma no debe caer con todo el peso.',
    ],
  },
  'Dumbbell_Lunges': {
    level: 'beginner',
    primaryMuscles: ['quadriceps'],
    secondaryMuscles: ['calves', 'glutes', 'hamstrings'],
    steps: [
      'De pie, con el torso erguido y una mancuerna en cada mano a los lados: es la posición inicial.',
      'Da un paso al frente de unos 60 cm con una pierna y baja el cuerpo mientras inspiras, manteniendo el torso recto y el equilibrio.',
      'La rodilla delantera no debe sobrepasar la punta del pie: mantén la espinilla vertical.',
      'Empuja sobre todo con el talón para volver a la posición inicial mientras espiras.',
      'Completa las repeticiones y repite con la otra pierna.',
    ],
  },
  'Romanian_Deadlift': {
    level: 'intermediate',
    primaryMuscles: ['hamstrings'],
    secondaryMuscles: ['calves', 'glutes', 'lower back'],
    steps: [
      'Con la barra en el suelo delante de ti, agárrala con agarre prono, algo más abierto que los hombros.',
      'Flexiona un poco las rodillas, con las espinillas verticales, la cadera atrás y la espalda recta: es la posición inicial.',
      'Con la espalda y los brazos siempre rectos, sube la barra con la cadera mientras espiras, de forma controlada y sin prisa.',
      'Ya erguido, inspira hondo, saca pecho y baja la barra empujando la cadera atrás, flexionando apenas las rodillas, sin hacer sentadilla.',
      'Aguanta el aire al bajar y espira al completar el movimiento.',
    ],
  },
  'Smith_Machine_Squat': {
    level: 'beginner',
    primaryMuscles: ['quadriceps'],
    secondaryMuscles: ['calves', 'glutes', 'hamstrings', 'lower back'],
    steps: [
      'Ajusta la altura de la barra en la multipower, carga el peso, métete debajo y apóyala en la parte alta de la espalda, justo bajo el cuello.',
      'Agárrala con las palmas al frente, desbloquéala y sácala empujando con las piernas mientras enderezas el torso.',
      'Pies a la anchura de los hombros con las puntas algo hacia fuera, cabeza alta y espalda recta: es la posición inicial.',
      'Inspira y baja despacio flexionando las rodillas, con la espalda recta, hasta pasar un poco de los 90°, sin que las rodillas sobrepasen la punta de los pies.',
      'Empuja el suelo con los talones y extiende las piernas mientras espiras hasta volver arriba.',
    ],
  },
  'Barbell_Squat': {
    level: 'beginner',
    primaryMuscles: ['quadriceps'],
    secondaryMuscles: ['calves', 'glutes', 'hamstrings', 'lower back'],
    steps: [
      'Mejor dentro de un rack. Coloca la barra justo por debajo de los hombros, cárgala, métete debajo y apóyala en la parte alta de la espalda, justo bajo el cuello.',
      'Sujétala con las dos manos y sácala del rack empujando con las piernas mientras enderezas el torso.',
      'Aléjate del rack con los pies a la anchura de los hombros y las puntas algo hacia fuera, cabeza alta y espalda recta: es la posición inicial.',
      'Inspira y baja despacio flexionando rodillas y cadera, con la espalda recta, hasta pasar un poco de los 90°, sin que las rodillas sobrepasen la punta de los pies.',
      'Empuja el suelo con los talones y extiende las piernas mientras espiras hasta volver arriba.',
    ],
  },
  'Dumbbell_Step_Ups': {
    level: 'intermediate',
    primaryMuscles: ['quadriceps'],
    secondaryMuscles: ['calves', 'glutes', 'hamstrings'],
    steps: [
      'De pie, erguido, con una mancuerna en cada mano y las palmas mirando a las piernas.',
      'Pon un pie en la plataforma y sube extendiendo la cadera y la rodilla, empujando sobre todo con el talón, mientras espiras. Apoya también el otro pie.',
      'Baja mientras inspiras: primero el pie que subió último, flexionando la cadera y la rodilla de la pierna de apoyo, y junta los pies abajo.',
      'Completa las repeticiones con una pierna y repite con la otra.',
    ],
  },
};
