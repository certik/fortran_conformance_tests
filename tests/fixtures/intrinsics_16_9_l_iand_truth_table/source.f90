! rule: S16.9.100-004
! covers: IAND-bit-truth-table
program i169l_iand_truth_table
  implicit none
  interface type_code
    procedure type_code_integer, type_code_real
  end interface
  integer :: checks
  integer :: left, right, got
  checks = 0
  left = ior(shiftl(1, 3), shiftl(1, 2))
  right = ior(shiftl(1, 3), shiftl(1, 1))
  got = iand(left, right)
  call require('IAND truth table keeps only one-one bit pairs', &
       btest(got, 3) .and. .not. btest(got, 2) .and. &
       .not. btest(got, 1) .and. .not. btest(got, 0), checks)
  if (checks /= 1) error stop
  write(*,'(a)') 'INTRINSICS 16.9 L IAND TRUTH TABLE OK'
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
end program i169l_iand_truth_table
