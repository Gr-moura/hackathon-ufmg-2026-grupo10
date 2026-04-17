import { Icon } from '../../../modules/ui/Icon';
import { useState } from 'react';


interface LoginInputsProps {
    inputType: "Login" | "Password";
    setValueFunction?: (value: string) => void;
}

export const LoginInputs = ({ inputType, setValueFunction }: LoginInputsProps) => {
    const [inputValue, setInputValue] = useState("");
    const [isPasswordVisible, setIsPasswordVisible] = useState(false);

    return (
        <div>
            <div className="login-screen__label-row">
				<label className="field-label" htmlFor="identifier">
					{inputType === "Login" ? "ID or Email Address" : "Password"}
				</label>
                {inputType === "Password" && (
                    <a href="/" className="pill" onClick={(event) => event.preventDefault()}>
                        Forgot?
                    </a>
                )}
            </div>
            <div className="input-row">
                {inputType === "Login" && (<>
                    <Icon name="person" className="icon-prefix" />
                    <input 
                        className="text-input" type="text" placeholder="username@bankufmg.com" 
                        value={inputValue} onChange={(e) => {setInputValue(e.target.value); if(setValueFunction) setValueFunction(e.target.value)}} 
                    />
                </>)}
                {inputType === "Password" && (<>
                    <Icon name="lock" className="icon-prefix" />
                    <input 
                        id="password" className="text-input" type={isPasswordVisible ? "text" : "password"} placeholder="••••••••••••" 
                        value={inputValue} onChange={(e) => {setInputValue(e.target.value); if(setValueFunction) setValueFunction(e.target.value)}}
                    />
                    <button 
                        type="button" className="icon-button icon-suffix" aria-label="Toggle password visibility"
                        onClick={() => setIsPasswordVisible((visible) => !visible)}
                    >
                        <Icon name={isPasswordVisible ? "visibility" : "visibility_off"} />
                    </button>
                </>)}
            </div>
        </div>
    )
};
