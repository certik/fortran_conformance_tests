! rule: S6.2.1-001
! covers: question-mark
! evidence: positive-control
! standard: f2023
program token_question_admission
    implicit none
    logical :: choose
    integer :: value

    choose = .true.
    value = (choose ? 17 : 29)
    if (value /= 17) error stop 1
    choose = .false.
    value = (choose ? 17 : 29)
    if (value /= 29) error stop 2
end program token_question_admission
