program data_statement_s008_boz_domain
  implicit none
  integer :: value
  data value /z'35'/
  if (radix(value) /= 2) error stop 1
  if (bit_size(value) < 6) error stop 2
  if (value /= 53) error stop 3
  write(*,'(a)') 'DATA STATEMENT S008 BOZ DOMAIN OK'
end program data_statement_s008_boz_domain
