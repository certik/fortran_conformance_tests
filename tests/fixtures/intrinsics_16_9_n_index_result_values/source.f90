! rule: S16.9.109-003
! covers: INDEX-string-shorter-than-substring-zero
program i169n_index_result_values
  implicit none
  integer :: checks
  checks = 0
  call require('INDEX shorter string than substring gives zero', index('AB', 'ABC') == 0, checks)
  if (checks /= 1) error stop
  write(*,'(a)') 'INTRINSICS 16.9 N INDEX RESULT VALUES OK'
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
end program i169n_index_result_values
