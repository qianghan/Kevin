import { AppProps } from 'next/app'
import { ChakraProvider } from '@chakra-ui/react'
import kaiTheme from '../theme'

function MyApp({ Component, pageProps }: AppProps) {
  return (
    <ChakraProvider resetCSS theme={kaiTheme}>
      <Component {...pageProps} />
    </ChakraProvider>
  )
}

export default MyApp 