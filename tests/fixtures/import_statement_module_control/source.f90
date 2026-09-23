module import_statement_c8100_module_scope
  implicit none
  integer, parameter :: value = 41
end module import_statement_c8100_module_scope

program import_statement_c8100_module_control
  use import_statement_c8100_module_scope, only: value
  implicit none
  if (value /= 41) error stop 1
  write(*,'(a)') 'IMPORT STATEMENT C8100 MODULE CONTROL OK'
end program import_statement_c8100_module_control
