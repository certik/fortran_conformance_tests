! rule: S16.9.110-003
! covers: INT-integer-identity
! covers: INT-real-magnitude-less-than-one-zero
! covers: INT-real-truncates-toward-zero
! covers: INT-complex-uses-real-part
program i169n_int_value_rules
  implicit none
  integer :: checks
  checks = 0
  call require('INT integer argument is identity', int(-42) == -42, checks)
  call require('INT real magnitude less than one gives zero', &
       int(0.5) == 0 .and. int(-0.5) == 0, checks)
  call require('INT real truncates toward zero exactly', &
       int(3.75) == 3 .and. int(-3.75) == -3, checks)
  call require('INT complex argument uses real part', int(cmplx(-3.75, 99.0)) == -3, checks)
  if (checks /= 4) error stop
  write(*,'(a)') 'INTRINSICS 16.9 N INT VALUE RULES OK'
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
end program i169n_int_value_rules
