module save_result_conflict_mod
contains
  function saved_result() result(answer)
    implicit none
    integer :: answer
    save :: answer
    answer = 7
  end function saved_result
end module save_result_conflict_mod
