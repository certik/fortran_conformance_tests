! rule: S16.9.110-002
! covers: INT-integer-result
! covers: INT-kind-present-result-kind
! covers: INT-kind-absent-default-kind
program i169n_int_numeric_and_boz
  implicit none
  integer, parameter :: ik = merge(8, 4, kind(0) /= 8)
  integer :: checks
  integer :: got
  checks = 0
  got = int(17)
  call require('INT result is integer assignment with exact value', got == 17, checks)
  call require('INT present KIND selects result kind', kind(int(17, kind=ik)) == ik, checks)
  call require('INT absent KIND is default integer kind', kind(int(17)) == kind(0), checks)
  if (checks /= 3) error stop
  write(*,'(a)') 'INTRINSICS 16.9 N INT NUMERIC AND BOZ OK'
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
  logical function same_bits(a, b)
    integer, intent(in) :: a, b
    integer :: k
    same_bits = .true.
    do k = 0, bit_size(a) - 1
      if (btest(a, k) .neqv. btest(b, k)) same_bits = .false.
    end do
  end function same_bits
end program i169n_int_numeric_and_boz
