import type { ExerciseGuide } from './types';

// Free Exercise DB (public domain): level and muscles as published;
// steps translated to Spanish and condensed from its instructions.
export const ARMS_GUIDES: Record<string, ExerciseGuide> = {
  'Barbell_Curl': {
    level: 'beginner',
    primaryMuscles: ['biceps'],
    secondaryMuscles: ['forearms'],
    steps: [
      'De pie, con el torso erguido, sujeta la barra a la anchura de los hombros con las palmas al frente y los codos pegados al torso; es la posición inicial.',
      'Con los brazos fijos, espira y sube la barra contrayendo los bíceps; solo se mueven los antebrazos.',
      'Sigue hasta que la barra llegue a la altura de los hombros, aprieta los bíceps y aguanta un segundo.',
      'Inspira y baja la barra despacio a la posición inicial.',
    ],
  },
  'Standing_Biceps_Cable_Curl': {
    level: 'beginner',
    primaryMuscles: ['biceps'],
    secondaryMuscles: [],
    steps: [
      'De pie, con el torso erguido, coge la barra de la polea baja a la anchura de los hombros con agarre supino y los codos pegados al torso; es la posición inicial.',
      'Con los brazos fijos, espira y sube la barra contrayendo los bíceps; solo se mueven los antebrazos.',
      'Sigue hasta que la barra llegue a la altura de los hombros, aprieta los bíceps y aguanta un segundo.',
      'Inspira y baja la barra despacio a la posición inicial.',
    ],
  },
  'Cable_Rope_Overhead_Triceps_Extension': {
    level: 'beginner',
    primaryMuscles: ['triceps'],
    secondaryMuscles: [],
    steps: [
      'Engancha la cuerda a la polea baja y cógela con las dos manos con agarre neutro.',
      'Extiende los brazos por encima de la cabeza, con los codos cerca de la cabeza y los nudillos hacia el techo; es la posición inicial.',
      'Con los brazos fijos, inspira y baja la cuerda despacio por detrás de la cabeza; haz una pausa cuando notes los tríceps estirados.',
      'Espira y vuelve a la posición inicial contrayendo los tríceps.',
    ],
  },
  'Close-Grip_Barbell_Bench_Press': {
    level: 'beginner',
    primaryMuscles: ['triceps'],
    secondaryMuscles: ['chest', 'shoulders'],
    steps: [
      'Túmbate en un banco plano, coge la barra con agarre estrecho, a la anchura de los hombros, sácala del soporte y sujétala sobre ti con los brazos bloqueados.',
      'Inspira y baja despacio hasta notar la barra en la mitad del pecho, con los codos pegados al torso para cargar los tríceps.',
      'Tras un segundo de pausa, espira y empuja la barra con los tríceps hasta bloquear los brazos; aguanta un segundo.',
      'La bajada debe durar al menos el doble que la subida; al terminar, deja la barra en el soporte.',
    ],
  },
  'Concentration_Curls': {
    level: 'beginner',
    primaryMuscles: ['biceps'],
    secondaryMuscles: ['forearms'],
    steps: [
      'Siéntate en un banco plano con las piernas abiertas y una mancuerna en el suelo entre ellas.',
      'Coge la mancuerna y apoya la parte trasera del brazo en la cara interna del muslo, con la palma al frente y el brazo extendido; es la posición inicial.',
      'Con el brazo fijo, espira y sube la mancuerna contrayendo el bíceps hasta la altura del hombro; solo se mueve el antebrazo.',
      'Arriba, el meñique debe quedar más alto que el pulgar; aprieta el bíceps un segundo.',
      'Inspira y baja despacio sin balancear; al terminar la serie, repite con el otro brazo.',
    ],
  },
  'Push-Ups_-_Close_Triceps_Position': {
    level: 'intermediate',
    primaryMuscles: ['triceps'],
    secondaryMuscles: ['chest', 'shoulders'],
    steps: [
      'Ponte en posición de flexión con las manos más juntas que la anchura de los hombros y el torso sostenido con los brazos extendidos.',
      'Inspira y baja hasta que el pecho casi toque el suelo.',
      'Espira y empuja con los tríceps y parte del pecho hasta volver arriba, apretando el pecho.',
      'Haz una pausa de un segundo arriba y repite.',
    ],
  },
  'Dumbbell_Bicep_Curl': {
    level: 'beginner',
    primaryMuscles: ['biceps'],
    secondaryMuscles: ['forearms'],
    steps: [
      'De pie, erguido, con una mancuerna en cada mano y los brazos extendidos, codos pegados al torso y palmas al frente; es la posición inicial.',
      'Con los brazos fijos, espira y sube las mancuernas contrayendo los bíceps hasta la altura de los hombros.',
      'Aprieta los bíceps un instante arriba.',
      'Inspira y baja las mancuernas despacio a la posición inicial.',
    ],
  },
  'Hammer_Curls': {
    level: 'beginner',
    primaryMuscles: ['biceps'],
    secondaryMuscles: [],
    steps: [
      'De pie, erguido, con una mancuerna en cada mano, brazos extendidos, codos pegados al torso y palmas mirando al cuerpo; es la posición inicial.',
      'Con el brazo fijo, espira y sube la mancuerna contrayendo el bíceps hasta la altura del hombro; mueve solo el antebrazo.',
      'Aprieta el bíceps un instante arriba.',
      'Inspira y baja las mancuernas despacio a la posición inicial.',
    ],
  },
  'Incline_Dumbbell_Curl': {
    level: 'beginner',
    primaryMuscles: ['biceps'],
    secondaryMuscles: [],
    steps: [
      'Siéntate en un banco inclinado con una mancuerna en cada mano y los brazos extendidos, codos pegados al torso y palmas al frente; es la posición inicial.',
      'Con los brazos fijos, espira y sube las mancuernas contrayendo los bíceps hasta la altura de los hombros; solo se mueven los antebrazos.',
      'Aguanta un segundo arriba.',
      'Inspira y baja las mancuernas despacio a la posición inicial.',
    ],
  },
  'Preacher_Curl': {
    level: 'beginner',
    primaryMuscles: ['biceps'],
    secondaryMuscles: [],
    steps: [
      'Coge la barra EZ por el agarre interior estrecho, palmas al frente y algo giradas hacia dentro por la forma de la barra; mejor si te la dan.',
      'Apoya los brazos y el pecho en la almohadilla del banco Scott y sujeta la barra a la altura de los hombros; es la posición inicial.',
      'Inspira y baja la barra despacio hasta extender los brazos y estirar del todo los bíceps.',
      'Espira y sube el peso con los bíceps hasta la altura de los hombros; aprieta fuerte y aguanta un segundo.',
    ],
  },
  'Reverse_Barbell_Curl': {
    level: 'beginner',
    primaryMuscles: ['biceps'],
    secondaryMuscles: ['forearms'],
    steps: [
      'De pie, con el torso erguido, sujeta la barra a la anchura de los hombros con agarre prono y los codos pegados al torso; es la posición inicial.',
      'Con los brazos fijos, espira y sube la barra contrayendo los bíceps hasta la altura de los hombros; solo se mueven los antebrazos.',
      'Aprieta un segundo arriba.',
      'Inspira y baja la barra despacio a la posición inicial.',
    ],
  },
  'EZ-Bar_Skullcrusher': {
    level: 'beginner',
    primaryMuscles: ['triceps'],
    secondaryMuscles: ['forearms'],
    steps: [
      'Túmbate en el banco, coge la barra EZ con agarre estrecho y sujétala con los brazos perpendiculares al suelo y los codos cerrados; es la posición inicial.',
      'Con los brazos fijos, inspira y baja la barra flexionando los codos; haz una pausa justo encima de la frente.',
      'Espira y extiende los codos para volver a la posición inicial.',
    ],
  },
  'Dips_-_Triceps_Version': {
    level: 'beginner',
    primaryMuscles: ['triceps'],
    secondaryMuscles: ['chest', 'shoulders'],
    steps: [
      'Sujétate en las barras con los brazos extendidos y casi bloqueados; es la posición inicial.',
      'Inspira y baja despacio con el torso erguido y los codos pegados al cuerpo para centrar el trabajo en los tríceps.',
      'Baja hasta que el codo forme 90°.',
      'Espira y empuja con los tríceps hasta volver a la posición inicial.',
    ],
  },
  'Standing_Dumbbell_Triceps_Extension': {
    level: 'beginner',
    primaryMuscles: ['triceps'],
    secondaryMuscles: [],
    steps: [
      'De pie, con los pies a la anchura de los hombros, coge una mancuerna con las dos manos y súbela por encima de la cabeza hasta extender los brazos.',
      'Apoya el disco superior en las palmas, con los pulgares alrededor del mango y las palmas hacia el techo; es la posición inicial.',
      'Con los brazos pegados a la cabeza y los codos arriba, inspira y baja la mancuerna en semicírculo por detrás hasta que los antebrazos toquen los bíceps.',
      'Solo se mueven los antebrazos; espira y sube la mancuerna con los tríceps a la posición inicial.',
    ],
  },
  'Triceps_Pushdown': {
    level: 'beginner',
    primaryMuscles: ['triceps'],
    secondaryMuscles: [],
    steps: [
      'Engancha una barra recta o angulada a la polea alta y cógela con agarre prono a la anchura de los hombros.',
      'De pie, erguido y apenas inclinado al frente, pega los brazos al cuerpo con los antebrazos apuntando a la polea; es la posición inicial.',
      'Espira y baja la barra con los tríceps hasta tocar los muslos y extender los brazos; los codos no se mueven del costado.',
      'Aguanta un segundo abajo e inspira mientras subes la barra despacio a la posición inicial.',
    ],
  },
  'Machine_Bicep_Curl': {
    level: 'beginner',
    primaryMuscles: ['biceps'],
    secondaryMuscles: [],
    steps: [
      'Ajusta el asiento a tu altura y elige el peso.',
      'Apoya los brazos en la almohadilla y coge las asas; es la posición inicial.',
      'Flexiona los codos llevando los antebrazos hacia los brazos.',
      'Haz una pausa arriba y baja el peso despacio a la posición inicial.',
      'Hasta acabar la serie, no dejes que el peso apoye del todo en los topes para mantener la tensión.',
    ],
  },
  'Machine_Triceps_Extension': {
    level: 'beginner',
    primaryMuscles: ['triceps'],
    secondaryMuscles: [],
    steps: [
      'Ajusta el asiento a tu altura y elige el peso.',
      'Apoya los brazos en la almohadilla y coge las asas; es la posición inicial.',
      'Extiende los codos alejando los antebrazos de los brazos.',
      'Haz una pausa al final del recorrido y vuelve despacio a la posición inicial.',
      'Hasta acabar la serie, no dejes que el peso apoye del todo en los topes para mantener la tensión.',
    ],
  },
};
