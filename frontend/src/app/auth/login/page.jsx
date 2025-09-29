import LoginForm from '@/components/forms/LoginForm';
import styles from '@/styles/LoginPage.module.css';
import Image from 'next/image';

export default function LoginPage() {
  const imageUrl = '/real-estate/real-estate.jpg';

  return (
    <div className={styles.background}>
      <h1 className={styles.title}>Estate</h1>
      <div className={styles.container}>
        <div className={styles.formContainer}>
          <LoginForm />
        </div>
        <div className={styles.image}>
          <Image
            src={imageUrl}
            alt="Modern city buildings representing real estate"
            width={669}
            height={746}
            priority // Load image first
          />
        </div>
      </div>
    </div>
  );
}
