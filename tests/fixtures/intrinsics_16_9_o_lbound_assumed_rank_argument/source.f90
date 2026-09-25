program i169o_lbound_assumed_rank_argument
  implicit none
  integer :: explicit_array(2:4) = [21, 22, 23]
  call require_true('lbound accepts ordinary array argument', lbound(explicit_array, dim=1) == 2)
  call check_assumed_rank(explicit_array)
  write(*,'(a)') 'INTRINSICS 16.9.O LBOUND ASSUMED RANK ARGUMENT OK'
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
  subroutine check_assumed_rank(x)
    integer, intent(in) :: x(..)
    call require_true('lbound accepts assumed-rank rank-one argument', &
        rank(x) == 1 .and. size(lbound(x)) == 1 .and. lbound(x, dim=1) == 1)
  end subroutine check_assumed_rank
end program i169o_lbound_assumed_rank_argument
