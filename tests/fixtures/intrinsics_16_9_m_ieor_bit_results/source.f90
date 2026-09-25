! rule: S16.9.106-004
! covers: IEOR-exclusive-or-truth-table
! covers: IEOR-negative-operand-bit-pattern
program i169m_ieor_bit_results
  implicit none
  integer :: pos, checks
  logical :: all_ones, all_zero
  checks = 0
  call require('IEOR exclusive OR truth table bits', &
       btest(ieor(1, 0), 0) .and. btest(ieor(0, 2), 1) .and. &
       .not. btest(ieor(1, 1), 0) .and. .not. btest(ieor(0, 0), 0) .and. ieor(1, 3) == 2, checks)
  all_ones = .true.
  all_zero = .true.
  do pos = 0, bit_size(0) - 1
    all_ones = all_ones .and. (btest(ieor(-1, 0), pos) .eqv. btest(-1, pos))
    all_zero = all_zero .and. .not. btest(ieor(-1, -1), pos)
  end do
  call require('IEOR negative operand bit patterns are combined bitwise', all_ones .and. all_zero, checks)
  if (checks /= 2) error stop
  write(*,'(a)') 'INTRINSICS 16.9 M IEOR BIT RESULTS OK'
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
end program i169m_ieor_bit_results
