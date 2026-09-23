subroutine import_statement_c8100_external(value)
  import
  implicit none
  integer, intent(out) :: value
  value = 37
end subroutine import_statement_c8100_external

program import_statement_c8100_external_control
  implicit none
  integer :: value
  value = -77
  call import_statement_c8100_external(value)
  if (value /= 37) error stop 1
  write(*,'(a)') 'IMPORT STATEMENT C8100 EXTERNAL CONTROL OK'
end program import_statement_c8100_external_control
