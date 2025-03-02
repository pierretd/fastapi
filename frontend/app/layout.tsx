import "./globals.css";
import { Inter, Montserrat } from "next/font/google";

const inter = Inter({ 
  subsets: ["latin"],
  variable: '--font-inter',
  display: 'swap',
});

const montserrat = Montserrat({
  subsets: ["latin"],
  variable: '--font-montserrat',
  display: 'swap',
  weight: ['400', '500', '600', '700'],
});

export const metadata = {
  title: "Steam Game Discovery",
  description: "Discover your next favorite game on Steam",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        {/* Script to prevent flash of wrong theme */}
        <script
          dangerouslySetInnerHTML={{
            __html: `
              (function() {
                // Check local storage for theme preference
                var savedTheme = localStorage.getItem('theme');
                
                // Check system preference if there's no saved theme
                if (!savedTheme && window.matchMedia('(prefers-color-scheme: dark)').matches) {
                  savedTheme = 'dark';
                }

                // Apply dark class if needed
                if (savedTheme === 'dark') {
                  document.documentElement.classList.add('dark');
                }
              })();
            `,
          }}
        />
      </head>
      <body className={`${inter.variable} ${montserrat.variable} font-inter`}>
        {children}
      </body>
    </html>
  );
}
