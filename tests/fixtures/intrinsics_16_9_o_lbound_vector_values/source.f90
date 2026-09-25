program i169o_lbound_vector_values
  implicit none
  integer, parameter :: wide_k = selected_int_kind(18)
  integer :: a(-3:4, 7:9, 0:2)
  call require_true('lbound vector elements match dim inquiries', &
      size(lbound(a)) == 3 .and. all(lbound(a) == [lbound(a, dim=1), lbound(a, dim=2), lbound(a, dim=3)]))
  call require_true('lbound vector kind elements match selected kind inquiries', &
      kind(lbound(a, kind=wide_k)) == wide_k .and. &
      all(lbound(a, kind=wide_k) == [lbound(a, dim=1, kind=wide_k), lbound(a, dim=2, kind=wide_k), &
                                     lbound(a, dim=3, kind=wide_k)]))
  call check_assumed_shape(a)
  write(*,'(a)') 'INTRINSICS 16.9.O LBOUND VECTOR VALUES OK'
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
  subroutine check_assumed_shape(dummy)
    integer, intent(in) :: dummy(5:, :, 0:)
    call require_true('lbound assumed-shape uses dummy lower bounds', &
        all(lbound(dummy) == [5, 1, 0]) .and. lbound(dummy, dim=1) == 5 .and. &
        lbound(dummy, dim=2) == 1 .and. lbound(dummy, dim=3) == 0)
  end subroutine check_assumed_shape
end program i169o_lbound_vector_values
