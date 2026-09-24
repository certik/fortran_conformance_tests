! rule: S16.9.99-003
! covers: IALL-bitwise-and-all-elements
! covers: IALL-zero-size-identity-all-one-bits
program i169l_iall_full_reduction
  implicit none
  interface type_code
    procedure type_code_integer, type_code_real
  end interface
  integer :: checks
  integer :: empty(0)
  integer :: k
  checks = 0
  call require('IALL full reduction is bitwise AND of all elements', &
       btest(iall([14, 13, 11]), 3) .and. &
       .not. btest(iall([14, 13, 11]), 2) .and. &
       .not. btest(iall([14, 13, 11]), 1), checks)
  call require('IALL zero-size identity has all model bits set', &
       all([(btest(iall(empty), k) .eqv. btest(not(0), k), k = 0, 7)]) .and. &
       (btest(iall(empty), bit_size(0)-1) .eqv. btest(not(0), bit_size(0)-1)), checks)
  if (checks /= 2) error stop
  write(*,'(a)') 'INTRINSICS 16.9 L IALL FULL REDUCTION OK'
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
end program i169l_iall_full_reduction
