import { Icon } from '../../../modules/ui/Icon';
import { useState } from 'react';
import './LoginInputs.css';


interface LoginInputsProps {
    inputType: "Login" | "Password";
    placeholder?: string;
    value: string;
    onChange: (value: string) => void;
}

export const LoginInputs = ({ inputType, placeholder, value, onChange }: LoginInputsProps) => {
    const [isPasswordVisible, setIsPasswordVisible] = useState(false);

    return (
        <div>
            <div className="login-screen__label-row">
				<label className="field-label" htmlFor="identifier">
					{inputType === "Login" ? "E-mail ou ID" : "Senha"}
				</label>
                {inputType === "Password" && (
                    <a href="/" className="pill" onClick={(event) => event.preventDefault()}>
                        Esqueci a senha
                    </a>
                )}
            </div>
            <div className="input-row">
                {inputType === "Login" && (<>
                    <Icon name="person" className="icon-prefix" />
                    <input 
                        className="text-input" type="text" placeholder={placeholder || "username@banco.com"}
                        value={value} onChange={(e) => onChange(e.target.value)} 
                    />
                </>)}
                {inputType === "Password" && (<>
                    <Icon name="lock" className="icon-prefix" />
                    <input 
                        id="password" className="text-input" type={isPasswordVisible ? "text" : "password"} placeholder={placeholder || "••••••••••••"} 
                        value={value} onChange={(e) => onChange(e.target.value)}
                    />
                    <button 
                        type="button" className="icon-button icon-suffix" aria-label="Alternar visibilidade da senha"
                        onClick={() => setIsPasswordVisible((visible) => !visible)}
                    >
                        <Icon name={isPasswordVisible ? "visibility" : "visibility_off"} />
                    </button>
                </>)}
            </div>
        </div>
    )
};