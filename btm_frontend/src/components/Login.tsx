import { useForm } from "react-hook-form";

interface FormData{
  email:string,
  password:string,
}

const Login = () => {
    const { register, handleSubmit, formState: { errors } } = useForm<FormData>();
    const onSubmit = ( data:any ) => {
      console.log( data )
    }

    return (
      <div className="min-h-screen bg-gray-50 flex flex-col justify-center">
        <div className="max-w-md w-full mx-auto">
          <div className="text-3xl font-bold text-gray-900 mt-2 text-center">Beat The Market</div>
          <div className="text-center font-small text-x">win the market</div>
        </div>
        <div className="max-w-md w-full mx-auto mt-4 bg-white p-8 border border-gray-300">
          <form action="" className="space-y-6" onSubmit={handleSubmit(onSubmit)} >
            <div className="">
              <label htmlFor="" className="text-sm font-bold text-gray-600 block">Login Name</label>
              <input
                {...register("email",{
                  required: true,
                  maxLength: 100,
                }

                )}
                name="email"
                type="email" className="w-full p-2 border border-gray-300 rounded mt-1" />
                {errors.email && "Email is invalid"}
            </div>
            <div className="mt-4">
              <label htmlFor="" className="text-sm font-bold text-gray-600 block">Password</label>
              <input 
                {...register("password", {
                  required: true,
                  minLength:8,
                  maxLength:28
                })}
                name="password"
                type="password" className="w-full p-2 border border-gray-300 rounded mt-1" />
                {errors.password && "Password is invalid"}
            </div>
            <div className="mt-4">
              <button className="w-full py-2 px-4 bg-blue-600 hover:bg-blue-700 rounded-md text-white">Submit</button>            
            </div>
          </form>
        </div>
      </div>
    );
  }
  export default Login;
