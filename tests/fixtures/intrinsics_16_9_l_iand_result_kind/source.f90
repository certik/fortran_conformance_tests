! rule: S16.9.100-002
! covers: IAND-result-kind-from-non-boz-operand
program i169l_iand_result_kind
  implicit none
  interface type_code
    procedure type_code_integer, type_code_real
  end interface
  integer, parameter :: ik = merge(8, 4, kind(0) /= 8)
  integer :: checks
  integer(kind=ik) :: a, b
  checks = 0
  a = int(z'0A', kind=ik)
  b = int(z'0F', kind=ik)
  call require('IAND result kind follows non-BOZ operand', &
       kind(iand(a, b)) == ik .and. kind(iand(z'0F', a)) == ik, checks)
  if (checks /= 1) error stop
  write(*,'(a)') 'INTRINSICS 16.9 L IAND RESULT KIND OK'
contains
  subroutine require(label, condition, checks)
    character(len=*), intent(in) :: label
    logical, intent(in) :: condition
    integer, intent(inout) :: checks
    if (.not. condition) then
      write(*,'(a)') label
      error stop
    end if
    checks = checks + 1
  end subroutine require
  integer function type_code_integer(x)
    integer, intent(in) :: x
    type_code_integer = 1
  end function type_code_integer
  integer function type_code_real(x)
    real, intent(in) :: x
    type_code_real = 2
  end function type_code_real
end program i169l_iand_result_kind
