program i169o_is_contiguous_assumed_rank
  implicit none
  integer, target :: whole(6) = [1, 2, 3, 4, 5, 6]
  integer, pointer :: strided(:)
  strided => whole(1:6:2)
  call require_true('is_contiguous direct array argument admitted', is_contiguous(whole))
  call require_true('is_contiguous assumed-rank scalar rank-zero true', assumed_rank_contiguous(17))
  write(*,'(a)') 'INTRINSICS 16.9.O IS CONTIGUOUS ASSUMED RANK OK'
contains
  subroutine require_true(label, value)
    character(len=*), intent(in) :: label
    logical, intent(in) :: value
    if (.not. value) then
      write(*,'(a)') label
      error stop
    end if
  end subroutine require_true
  subroutine require_false(label, value)
    character(len=*), intent(in) :: label
    logical, intent(in) :: value
    if (value) then
      write(*,'(a)') label
      error stop
    end if
  end subroutine require_false
  logical function assumed_rank_contiguous(x)
    integer, intent(in) :: x(..)
    assumed_rank_contiguous = is_contiguous(x)
  end function assumed_rank_contiguous
end program i169o_is_contiguous_assumed_rank
