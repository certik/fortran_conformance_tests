program i169o_lbound_dim_values
  implicit none
  integer :: whole(-3:4, 7:9)
  integer :: zero_extent(5:4)
  call require_true('lbound dim whole nonzero extent returns declared lower bounds', &
      lbound(whole, dim=1) == -3 .and. lbound(whole, dim=2) == 7)
  call check_assumed_size(whole)
  call require_true('lbound dim otherwise returns one for section and zero extent', &
      lbound(whole(-3:4:2, 7:9), dim=1) == 1 .and. lbound(zero_extent, dim=1) == 1)
  write(*,'(a)') 'INTRINSICS 16.9.O LBOUND DIM VALUES OK'
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
  subroutine check_assumed_size(dummy)
    integer, intent(in) :: dummy(2:*)
    call require_true('lbound assumed-size rank dim lower bound', lbound(dummy, dim=1) == 2)
  end subroutine check_assumed_size
end program i169o_lbound_dim_values
