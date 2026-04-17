import { Icon } from '../../modules/ui/Icon';
import { LoginInputs } from '../../modules/ui/LoginInputs/LoginInputs';
import { LoginRoleSelector } from '../../modules/ui/LoginRoleSelector/LoginRoleSelector';
import './LoginScreen.css';


export function LoginScreen() {

	return (
		<main className="login-wrap login-screen">
		<div className="login-shell login-screen__shell">
			<div className="login-screen__hero">
			<h1 className="headline login-screen__headline">
				EnterOS <span className="accent">Enterprise Legal Operations</span>
			</h1>
			<p className="lede login-screen__lede">
				Access the case workspace, load autos and subsídios, then inspect the AI recommendation before making a decision.
			</p>
			</div>

			<section className="login-card login-screen__card">
			<LoginRoleSelector onSelectRole={(role) => console.log("selected role: ", role)} />

			<div className="form-grid login-screen__form">

				<LoginInputs inputType='Login'></LoginInputs>
				<LoginInputs inputType='Password'></LoginInputs>

				<label className="checkbox-row">
				<input type="checkbox" />
				<span className="muted login-screen__remember">Keep me authenticated for 24 hours</span>
				</label>

				<button type="button" className="access-button" onClick={() => navigation.navigate("dashboard")}>
					Access System
				</button>
			</div>

			<div className="login-screen__footer">
				<p className="muted login-screen__footer-text">
				Internal enterprise access only. <a href="/" onClick={(event) => event.preventDefault()} style={{ color: 'var(--secondary)', fontWeight: 700 }}>Request access credentials</a>
				</p>
			</div>
			</section>
		</div>
		</main>
	);
}