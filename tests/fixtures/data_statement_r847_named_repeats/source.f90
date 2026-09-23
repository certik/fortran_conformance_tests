program data_statement_r847_named_repeats
  implicit none
  integer, parameter :: n = 2
  integer :: literal(2), named(2)
  data literal /2*53/
  data named /n*59/
  if (literal(1) /= 53) error stop 1
  if (literal(2) /= 53) error stop 2
  if (named(1) /= 59) error stop 3
  if (named(2) /= 59) error stop 4
  write(*,'(a)') 'DATA STATEMENT R847 NAMED REPEATS OK'
end program data_statement_r847_named_repeats
