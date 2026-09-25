! rule: S16.9.109-004
! covers: INDEX-forward-smallest-position
! covers: INDEX-backward-greatest-position
! covers: INDEX-empty-substring-forward-one
! covers: INDEX-empty-substring-backward-len-plus-one
program i169n_index_back_empty_values
  implicit none
  integer :: checks
  checks = 0
  call require('INDEX forward smallest matching position', index('ABABA', 'BA') == 2, checks)
  call require('INDEX backward greatest matching position', index('ABABA', 'BA', back=.true.) == 4, checks)
  call require('INDEX empty substring forward gives one', index('ABCD', '', back=.false.) == 1, checks)
  call require('INDEX empty substring backward gives length plus one', &
       index('ABCD', '', back=.true.) == len('ABCD') + 1, checks)
  if (checks /= 4) error stop
  write(*,'(a)') 'INTRINSICS 16.9 N INDEX BACK EMPTY VALUES OK'
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
end program i169n_index_back_empty_values
