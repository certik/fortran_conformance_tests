! rule: S16.9.98-005
! covers: IACHAR-LLE-implies-code-le
! covers: IACHAR-LGE-implies-code-ge
! covers: IACHAR-equality-consistent-codes
program i169l_iachar_lexical_consistency
  implicit none
  interface type_code
    procedure type_code_integer, type_code_real
  end interface
  integer :: checks
  checks = 0
  call require('IACHAR codes follow LLE ordering', &
       lle('A','B') .and. iachar('A') <= iachar('B'), checks)
  call require('IACHAR codes follow LGE ordering', &
       lge('X','0') .and. iachar('X') >= iachar('0'), checks)
  call require('IACHAR equal characters have equal codes', &
       lle('X','X') .and. lge('X','X') .and. iachar('X') == iachar('X'), checks)
  if (checks /= 3) error stop
  write(*,'(a)') 'INTRINSICS 16.9 L IACHAR LEXICAL CONSISTENCY OK'
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
end program i169l_iachar_lexical_consistency
