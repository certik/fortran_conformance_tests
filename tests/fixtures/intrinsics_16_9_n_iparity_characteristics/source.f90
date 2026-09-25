! rule: S16.9.112-002
! covers: IPARITY-result-same-type-kind-as-array
! covers: IPARITY-result-scalar-without-dim
! covers: IPARITY-result-rank-and-shape-with-dim
program i169n_iparity_characteristics
  implicit none
  integer, parameter :: ik = merge(8, 4, kind(0) /= 8)
  integer :: checks
  integer(kind=ik) :: wide(3)
  integer :: a(2,3)
  checks = 0
  wide = [1_ik, 2_ik, 4_ik]
  a = reshape([1, 2, 4, 8, 16, 32], [2, 3])
  call require('IPARITY result has same kind as ARRAY', kind(iparity(wide)) == ik, checks)
  call require('IPARITY without DIM is scalar', size(shape(iparity(a))) == 0, checks)
  call require('IPARITY with DIM has rank one and remaining shape', &
       size(shape(iparity(a, dim=1))) == 1 .and. all(shape(iparity(a, dim=1)) == [3]), checks)
  if (checks /= 3) error stop
  write(*,'(a)') 'INTRINSICS 16.9 N IPARITY CHARACTERISTICS OK'
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
end program i169n_iparity_characteristics
