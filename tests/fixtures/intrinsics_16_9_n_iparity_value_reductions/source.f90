! rule: S16.9.112-003
! covers: IPARITY-all-elements-exclusive-or
! covers: IPARITY-zero-size-array-zero
program i169n_iparity_value_reductions
  implicit none
  integer :: checks
  integer, allocatable :: empty(:)
  checks = 0
  allocate(empty(0))
  call require('IPARITY all elements are exclusive OR reduced', &
       same_bits(iparity([14, 13, 8]), ieor(ieor(14, 13), 8)), checks)
  call require('IPARITY zero-size array has zero value', &
       popcnt(iparity(empty)) == 0 .and. popcnt(iparity([1, 2, 4])) == 3, checks)
  if (checks /= 2) error stop
  write(*,'(a)') 'INTRINSICS 16.9 N IPARITY VALUE REDUCTIONS OK'
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
end program i169n_iparity_value_reductions
