program i169o_is_contiguous_values
  implicit none
  integer, target :: target(10) = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
  integer, pointer :: contiguous_pointer(:)
  integer, pointer :: strided_pointer(:)
  contiguous_pointer => target
  strided_pointer => target(1:10:2)
  call require_true('is_contiguous associated pointer argument true for whole target', &
      associated(contiguous_pointer) .and. is_contiguous(contiguous_pointer))
  call require_true('is_contiguous result default logical scalar', &
      kind(is_contiguous(target)) == kind(.false.) .and. rank(is_contiguous(target)) == 0)
  call require_true('is_contiguous whole nonpointer array is true', is_contiguous(target))
  call require_false('is_contiguous strided pointer section is false', is_contiguous(strided_pointer))
  write(*,'(a)') 'INTRINSICS 16.9.O IS CONTIGUOUS CHARACTERISTICS OK'
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
end program i169o_is_contiguous_values
