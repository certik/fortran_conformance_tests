program import_statement_c8100_main
  import
  implicit none
  integer :: value
  value = 31
  if (value /= 31) error stop 1
  write(*,'(a)') 'IMPORT STATEMENT C8100 MAIN CONTROL OK'
end program import_statement_c8100_main
