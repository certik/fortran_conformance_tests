! rule: S16.9.112-005
! covers: IPARITY-rank-one-dim-equals-no-dim
! covers: IPARITY-dim-vector-section-reduction
! covers: IPARITY-dim-mask-section-reduction
program i169n_iparity_dim_sections
  implicit none
  integer :: checks
  integer :: a(2,3)
  logical :: mask_cols(2,3)
  checks = 0
  a = reshape([1, 2, 4, 8, 16, 32], [2, 3])
  mask_cols = reshape([.true., .false., .false., .true., .true., .true.], [2, 3])
  call require('IPARITY rank-one DIM equals no-DIM reduction', &
       same_bits(iparity([1, 2, 4], dim=1), iparity([1, 2, 4])), checks)
  call require('IPARITY DIM reduces each vector section', &
       all(iparity(a, dim=1) == [3, 12, 48]) .and. all(iparity(a, dim=2) == [21, 42]), checks)
  call require('IPARITY DIM with MASK reduces masked vector sections', &
       all(iparity(a, dim=1, mask=mask_cols) == [1, 8, 48]), checks)
  if (checks /= 3) error stop
  write(*,'(a)') 'INTRINSICS 16.9 N IPARITY DIM SECTIONS OK'
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
end program i169n_iparity_dim_sections
