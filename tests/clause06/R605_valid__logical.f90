! rule: R605
! covers: logical-literal
! evidence: positive-control
program logical_literal_alternative
    implicit none
    logical :: truth, falsehood
    data truth /.true./
    data falsehood /.false./

    if (.not. truth) error stop 1
    if (falsehood) error stop 2
end program logical_literal_alternative
