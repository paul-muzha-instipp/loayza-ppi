/*!
* Start Bootstrap - Shop Homepage v5.0.6 (https://startbootstrap.com/template/shop-homepage)
* Copyright 2013-2023 Start Bootstrap
* Licensed under MIT (https://github.com/StartBootstrap/startbootstrap-shop-homepage/blob/master/LICENSE)
*/
// This file is intentionally blank
// Use this file to add JavaScript to your project

document.addEventListener('DOMContentLoaded', () => {
    // 1. Elementos del DOM
    const carouselContainer = document.querySelector('.scrolling-carousel-container');
    const leftArrow = document.querySelector('.left-arrow');
    const rightArrow = document.querySelector('.right-arrow');
    const wrapper = document.querySelector('.scrolling-carousel-wrapper');
    
    // 2. Configuración para movimiento continuo
    // Velocidad: 1px cada 25 milisegundos = 40 píxeles por segundo (movimiento suave)
    const stepSize = 1;         // Mueve 1 píxel por cada intervalo
    const intervalTime = 25;    // Intervalo de tiempo en milisegundos (25ms para suavidad)
    const manualScrollAmount = 180; // Distancia para el desplazamiento con flechas (manual)

    let scrollInterval;

    // Lógica de Desplazamiento Manual (Flechas)
    const manualScroll = (direction) => {
        // Pausar el carrusel automático
        clearInterval(scrollInterval); 
        scrollInterval = null;
        
        // Ejecutar el desplazamiento manual con animación suave
        const scrollDistance = direction === 'right' ? manualScrollAmount : -manualScrollAmount;
        carouselContainer.scrollBy({
            left: scrollDistance,
            behavior: 'smooth'
        });
        
        // Reiniciar el movimiento continuo después de un breve retraso
        setTimeout(startAutoScroll, 4000); // 4 segundos después de la interacción manual
    };

    rightArrow.addEventListener('click', () => manualScroll('right'));
    leftArrow.addEventListener('click', () => manualScroll('left'));


    // Lógica de Desplazamiento Automático (Continuo)
    const autoScrollStep = () => {
        // Verifica si hemos llegado al final. Si es así, regresa instantáneamente al inicio.
        // Restamos 1 al scrollWidth para manejar posibles errores de redondeo del navegador.
        if (carouselContainer.scrollLeft >= (carouselContainer.scrollWidth - carouselContainer.clientWidth - 1)) {
            // Regreso instantáneo al principio (efecto loop infinito)
            carouselContainer.scrollLeft = 0;
        } else {
            // Desplazamiento continuo de 1 píxel
            carouselContainer.scrollLeft += stepSize;
        }
    };

    const startAutoScroll = () => {
        // Sólo inicia si no hay un intervalo ya corriendo
        if (!scrollInterval) {
            // Usamos setInterval para mover el carrusel en cada intervalo
            scrollInterval = setInterval(autoScrollStep, intervalTime);
        }
    };
    // Pausa al Pasar el Ratón (UX)
    wrapper.addEventListener('mouseenter', () => {
        clearInterval(scrollInterval);
        scrollInterval = null; 
    });

    // Reanuda al Salir el Ratón
    wrapper.addEventListener('mouseleave', () => {
        startAutoScroll();
    });
    
    // Iniciar el desplazamiento automático al cargar la página
    startAutoScroll();
});