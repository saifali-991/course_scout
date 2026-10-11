import { useEffect, useRef, useState } from 'react';

/** Landscape clip for normal/desktop viewports (Cloudinary, q_auto = smaller bytes). */
const DESKTOP_SRC =
  'https://res.cloudinary.com/xb5ardnn/video/upload/q_auto/v1791645452/1010_1.mp4';
/** Portrait clip for small / short viewports (bundled from public/). */
const PHONE_SRC = '/video/phone_video.mp4';
/** Switch to the phone clip only on genuinely phone-sized (narrow) viewports.
 *  Width-only on purpose: a `max-height` rule wrongly fires on maximised laptop
 *  browsers (viewport height is usually < 851px once the browser chrome is
 *  subtracted), which made the portrait clip show up on the desktop. 767px is
 *  the standard "mobile" boundary — every laptop/desktop is wider than this, so
 *  full-screen always gets the landscape Cloudinary clip. */
const SMALL_MQ = '(max-width: 767px)';


/**
 * Full-screen, looping background video.
 *
 * - Sits fixed behind all content (z-index: -1) so it never blocks clicks.
 * - autoPlay + muted + loop + playsInline → starts automatically, plays silently
 *   and loops forever. The browser fetches the file ONCE and then loops it from
 *   cache, so Cloudinary only sees a single request per page load (saves bandwidth).
 * - A translucent scrim on top keeps any text sitting over the video readable.
 * - Small/short viewports swap to a portrait clip. If that clip can't fill the
 *   screen it is centred and framed (decorative border); if it does fill the
 *   screen it plays full-bleed with no frame.
 *
 * NOTE on `muted`: React's `muted` JSX attribute is unreliable across browsers
 * (a known React issue) — it renders the attribute but doesn't always set the
 * `video.muted` property. When the video is actually un-muted, the browser's
 * autoplay policy blocks playback entirely and the video looks "stuck / not
 * looping". So we ALSO set muted/loop as properties via a ref and call play()
 * ourselves, which is the only reliable way to guarantee autoplay.
 */
export default function BackgroundVideo() {
  const videoRef = useRef(null);
  const [isSmall, setIsSmall] = useState(() =>
    typeof window !== 'undefined' ? window.matchMedia(SMALL_MQ).matches : false
  );

  // Follow the breakpoint live (rotate / resize / devtools).
  useEffect(() => {
    const mq = window.matchMedia(SMALL_MQ);
    const onChange = (e) => setIsSmall(e.matches);
    setIsSmall(mq.matches);
    mq.addEventListener('change', onChange);
    return () => mq.removeEventListener('change', onChange);
  }, []);

  // Reload the right source + guarantee silent autoplay + loop (as properties).
  useEffect(() => {
    const v = videoRef.current;
    if (!v) return;

    v.muted = true;
    v.defaultMuted = true;
    v.loop = true;
    v.load(); // pick up the <source> that matches the current breakpoint

    const tryPlay = () => {
      const p = v.play();
      if (p && typeof p.catch === 'function') p.catch(() => { /* ignore autoplay rejection */ });
    };

    if (v.readyState >= 2) tryPlay();
    else v.addEventListener('loadeddata', tryPlay, { once: true });

    return () => v.removeEventListener('loadeddata', tryPlay);
  }, [isSmall]);

  // Phone clip: frame it only when it can't fill the screen.
  useEffect(() => {
    const v = videoRef.current;
    if (!v) return;

    // Desktop → full-bleed cover; clear any phone-mode overrides.
    if (!isSmall) {
      v.style.width = '';
      v.style.height = '';
      v.style.left = '';
      v.style.top = '';
      v.classList.remove('is-framed');
      return;
    }

    const evaluate = () => {
      const parent = v.parentElement;
      if (!parent) return;
      const vw = v.videoWidth;
      const vh = v.videoHeight;
      const cw = parent.clientWidth;
      const ch = parent.clientHeight;
      if (!vw || !vh || !cw || !ch) return; // metadata not ready yet

      const videoAR = vw / vh;
      const boxAR = cw / ch;
      const fills = Math.abs(videoAR - boxAR) < 0.03; // close enough → covers

      if (fills) {
        v.style.width = '100%';
        v.style.height = '100%';
        v.style.left = '0px';
        v.style.top = '0px';
        v.classList.remove('is-framed');
      } else {
        // Largest centred rectangle that fits (contain).
        let w;
        let h;
        if (videoAR > boxAR) {
          w = cw;
          h = Math.round(cw / videoAR);
        } else {
          h = ch;
          w = Math.round(ch * videoAR);
        }
        v.style.width = `${w}px`;
        v.style.height = `${h}px`;
        v.style.left = `${Math.round((cw - w) / 2)}px`;
        v.style.top = `${Math.round((ch - h) / 2)}px`;
        v.classList.add('is-framed');
      }
    };

    v.addEventListener('loadedmetadata', evaluate);
    window.addEventListener('resize', evaluate);
    evaluate();
    return () => {
      v.removeEventListener('loadedmetadata', evaluate);
      window.removeEventListener('resize', evaluate);
    };
  }, [isSmall]);

  return (
    <div className="bg-video" aria-hidden="true">
      <video
        ref={videoRef}
        className={`bg-video__el${isSmall ? ' bg-video__el--phone' : ''}`}
        autoPlay
        muted
        loop
        playsInline
        preload="auto"
        disablePictureInPicture
      >
        <source src={isSmall ? PHONE_SRC : DESKTOP_SRC} type="video/mp4" />
      </video>
      <div className="bg-video__scrim" />
    </div>
  );
}
