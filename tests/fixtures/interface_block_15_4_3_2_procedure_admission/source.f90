module interface_block_procedure_admission_m
  implicit none
  ! rule: S15.4.3.2-002
  ! covers: procedure-stmt admitted in a generic interface block
  interface apply
    module procedure set_good
  end interface apply
contains
  subroutine set_good(x)
    integer, intent(out) :: x
    x = 23
  end subroutine set_good
  subroutine set_bad(x)
    integer, intent(out) :: x
    x = 22
  end subroutine set_bad
end module interface_block_procedure_admission_m

program interface_block_procedure_admission
  use interface_block_procedure_admission_m
  implicit none
  integer :: observed
  observed = -7
  call apply(observed)
  if (observed /= 23) error stop 1
  print '(a)', 'INTERFACE BLOCK PROCEDURE ADMISSION OK'
end program interface_block_procedure_admission
