import { Link } from 'react-router-dom';
import { PlayIcon } from './Icons.jsx';

const cols = [
  {
    title: 'Discover',
    links: [
      { label: 'Python courses', to: '/?q=Python' },
      { label: 'Data Analytics', to: '/?q=Data%20Analytics' },
      { label: 'Web Development', to: '/?q=Web%20Development' },
      { label: 'AI & Machine Learning', to: '/?q=Machine%20Learning' },
    ],
  },
  {
    title: 'Popular',
    links: [
      { label: 'Free courses', to: '/?free=free' },
      { label: 'Certificates', to: '/?q=Certificate' },
      { label: 'University courses', to: '/?q=University' },
      { label: 'All categories', to: '/categories' },
    ],
  },
  {
    title: 'Support',
    links: [
      { label: 'About CourseScout', to: '/' },
      { label: 'Saved resources', to: '/saved' },
      { label: 'Privacy Policy', to: '/' },
      { label: 'Terms of Service', to: '/' },
    ],
  },
];

export default function Footer() {
  return (
    <footer className="footer">
      <div className="container">
        <div className="footer__grid">
          <div className="footer__brand">
            <Link to="/" className="brand">
              <span className="brand__mark">
                <PlayIcon size={18} />
              </span>
              <span>
                Course<span className="brand__text--blue">Scout</span>
              </span>
            </Link>
            <p>The smartest way to find free and paid online courses from trusted platforms.</p>
          </div>

          {cols.map((col) => (
            <div className="footer__col" key={col.title}>
              <h4>{col.title}</h4>
              {col.links.map((l) => (
                <Link key={l.label} to={l.to}>
                  {l.label}
                </Link>
              ))}
            </div>
          ))}
        </div>

        <div className="footer__bottom">
          <span>© 2026 CourseScout. All rights reserved.</span>
          <span>Built with Django &amp; React</span>
        </div>
      </div>
    </footer>
  );
}
