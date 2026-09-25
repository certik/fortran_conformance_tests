! rule: S16.9.111-004
! covers: IOR-inclusive-or-truth-table
! covers: IOR-negative-operand-bit-pattern
program i169n_ior_truth_table
  implicit none
  integer :: checks
  checks = 0
  call require('IOR inclusive OR truth table sets either one bits', &
       btest(ior(5, 3), 0) .and. btest(ior(5, 3), 1) .and. btest(ior(5, 3), 2) .and. &
       popcnt(iand(ior(5, 3), 7)) == 3, checks)
  call require('IOR negative operand bit pattern keeps every one bit', &
       same_bits(ior(-1, 0), -1) .and. same_bits(ior(-1, -1), -1), checks)
  if (checks /= 2) error stop
  write(*,'(a)') 'INTRINSICS 16.9 N IOR TRUTH TABLE OK'
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
end program i169n_ior_truth_table
